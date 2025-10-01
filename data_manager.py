import asyncio
import aiosqlite
import os

# --- Constants ---
# Define the path to the SQLite database file.
DB_PATH = 'bible.db'

# --- Custom Exception ---
# Custom exception for when a verse cannot be found in the database.
class VerseNotFoundError(Exception):
    pass

# --- Caching Mechanism ---
# In-memory cache to store previously fetched scripture texts.
# This reduces database queries for frequently accessed verses.
scripture_cache = {}

# Dictionary to track in-flight requests.
# This prevents the same verse from being fetched multiple times concurrently (race condition).
ongoing_fetches = {}

async def _fetch_from_db(book, reference, translation="KJV"):
    """
    The internal function that connects to the database and performs the actual fetch.
    It supports single verses (e.g., "3:16") and ranges (e.g., "13:4-7").
    """
    print(f"Cache miss. Fetching {translation} {book} {reference} from database...")

    # --- Parse Reference ---
    # Split the reference into chapter and verse parts.
    try:
        chapter_str, verse_str = reference.split(':')
        chapter = int(chapter_str)
    except ValueError:
        raise VerseNotFoundError(f"Invalid reference format for '{book} {reference}'.")

    # --- Database Connection ---
    async with aiosqlite.connect(DB_PATH) as db:
        # Use row_factory to get results as dictionary-like objects.
        db.row_factory = aiosqlite.Row

        # --- Build and Execute Query ---
        # Check if the reference is a range (e.g., "4-7").
        if '-' in verse_str:
            try:
                start_verse, end_verse = map(int, verse_str.split('-'))
            except ValueError:
                raise VerseNotFoundError(f"Invalid verse range in '{book} {reference}'.")

            sql_query = """
                SELECT verse, text FROM bible_verses
                WHERE book = ? AND chapter = ? AND verse BETWEEN ? AND ? AND translation = ?
                ORDER BY verse;
            """
            cursor = await db.execute(sql_query, (book, chapter, start_verse, end_verse, translation))
            rows = await cursor.fetchall()

        # Otherwise, it's a single verse.
        else:
            try:
                verse = int(verse_str)
            except ValueError:
                raise VerseNotFoundError(f"Invalid verse number in '{book} {reference}'.")

            sql_query = """
                SELECT text FROM bible_verses
                WHERE book = ? AND chapter = ? AND verse = ? AND translation = ?;
            """
            cursor = await db.execute(sql_query, (book, chapter, verse, translation))
            rows = await cursor.fetchall()

        # --- Process Results ---
        if not rows:
            raise VerseNotFoundError(f"Verse '{translation} {book} {reference}' not found in the database.")

        # Format the text for display. For ranges, prefix each verse with its number.
        if '-' in verse_str:
            return " ".join([f"[{row['verse']}] {row['text']}" for row in rows])
        else:
            return rows[0]['text']


async def get_available_translations():
    """
    Asynchronously fetches a list of unique Bible translations from the database.
    """
    if not os.path.exists(DB_PATH):
        return ["KJV"] # Default if DB doesn't exist
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute("SELECT DISTINCT translation FROM bible_verses ORDER BY translation;")
        rows = await cursor.fetchall()
        return [row[0] for row in rows] if rows else ["KJV"]

async def get_scripture_text(book, reference, translation="KJV"):
    """
    Asynchronously gets scripture text from the database, with caching,
    error handling, and protection against race conditions.
    """
    # The cache key now includes the translation to avoid conflicts.
    cache_key = f"{translation}:{book.lower()}:{reference}"

    # --- Check Cache ---
    if cache_key in scripture_cache:
        print(f"Cache hit for {translation} {book} {reference}.")
        cached_value = scripture_cache[cache_key]
        # If the cached value is an error, re-raise it.
        if isinstance(cached_value, VerseNotFoundError):
            raise cached_value
        return cached_value

    # --- Check for Ongoing Fetches ---
    if cache_key in ongoing_fetches:
        print(f"Waiting for existing fetch for {translation} {book} {reference}...")
        return await ongoing_fetches[cache_key]

    # --- Fetch from Database ---
    # No cache hit and no ongoing fetch, so create a new database query task.
    task = asyncio.create_task(_fetch_from_db(book, reference, translation))
    ongoing_fetches[cache_key] = task

    try:
        # Wait for the database query to complete.
        result = await task
        # Store the successful result in the cache.
        scripture_cache[cache_key] = result
        return result
    except VerseNotFoundError as e:
        # If the verse wasn't found, cache the error to prevent future lookups.
        scripture_cache[cache_key] = e
        raise e
    finally:
        # Once the task is complete (either success or error), remove it from ongoing fetches.
        if cache_key in ongoing_fetches:
            del ongoing_fetches[cache_key]

async def main():
    """Example usage to demonstrate and test the async database functionality."""
    print("--- Requesting multiple verses from the database ---")

    async def fetch_and_print(book, ref, trans="KJV"):
        try:
            # Fetch the text using the main public function.
            text = await get_scripture_text(book, ref, trans)
            print(f"Success for {trans} {book} {ref}:\n  {text}\n")
        except VerseNotFoundError as e:
            print(f"Error for {trans} {book} {ref}: {e}\n")

    # --- Test Cases ---
    tasks = [
        # 1. Fetch a single verse (should be a cache miss then hit).
        fetch_and_print("John", "3:16"),
        fetch_and_print("John", "3:16"),
        # 2. Fetch a verse range.
        fetch_and_print("1 Corinthians", "13:4-7"),
        # 3. Fetch a verse that does not exist.
        fetch_and_print("Genesis", "1:99"),
        # 4. Fetch from a different translation.
        fetch_and_print("Genesis", "1:1", "YLT"),
        # 5. Test another concurrent request for an in-flight fetch.
        fetch_and_print("Romans", "8:28"),
        fetch_and_print("Romans", "8:28"),
    ]

    # Run all test tasks concurrently.
    await asyncio.gather(*tasks)

if __name__ == '__main__':
    # Ensure the database exists before running tests.
    if not os.path.exists(DB_PATH):
        print(f"Error: Database file '{DB_PATH}' not found.")
        print("Please run 'database_setup.py' and 'database_import.py' first.")
    else:
        asyncio.run(main())