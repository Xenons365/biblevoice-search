import asyncio
import re
from database import get_verse, get_verses_in_range

# Custom exception for API errors
class VerseNotFoundError(Exception):
    pass

# In-memory cache for scripture texts
scripture_cache = {}
# Dictionary to track in-flight requests to prevent race conditions
ongoing_fetches = {}

async def _fetch_from_db(book, reference):
    """
    The internal function that performs the actual fetch from the SQLite database.
    This is now a non-blocking, async function.
    """
    print(f"Cache miss. Fetching {book} {reference} from database...")

    # Regex to parse chapter, verse, and optional end_verse
    match = re.match(r"(\d+):(\d+)(?:-(\d+))?", reference)
    if not match:
        raise VerseNotFoundError(f"Invalid reference format: {reference}")

    chapter = int(match.group(1))
    start_verse = int(match.group(2))
    end_verse = match.group(3)

    try:
        if end_verse:
            # This is a range query
            end_verse = int(end_verse)
            verses = await asyncio.to_thread(get_verses_in_range, book, chapter, start_verse, end_verse)
            if not verses:
                raise VerseNotFoundError(f"Verses {book} {reference} not found.")
            # Format the output for a range
            return "\n".join(f"{book} {chapter}:{start_verse+i} {text}" for i, text in enumerate(verses))
        else:
            # This is a single verse query
            verse_text = await asyncio.to_thread(get_verse, book, chapter, start_verse)
            if "not found" in verse_text: # Check for the not found message from the db function
                raise VerseNotFoundError(f"Verse {book} {reference} not found.")
            return verse_text
    except Exception as e:
        # Catch any other database-related errors
        raise VerseNotFoundError(f"An error occurred while fetching {book} {reference}: {e}")


async def get_scripture_text(book, reference):
    """
    Asynchronously gets scripture text from the local database, with caching
    and protection against race conditions.
    """
    cache_key = f"{book.lower().strip()}:{reference.strip()}"

    if cache_key in scripture_cache:
        print(f"Cache hit for {book} {reference}.")
        cached_value = scripture_cache[cache_key]
        if isinstance(cached_value, VerseNotFoundError):
            raise cached_value
        return cached_value

    if cache_key in ongoing_fetches:
        print(f"Waiting for existing fetch for {book} {reference}...")
        return await ongoing_fetches[cache_key]

    # No cache hit and no ongoing fetch, so create a new one.
    task = asyncio.create_task(_fetch_from_db(book, reference))
    ongoing_fetches[cache_key] = task

    try:
        result = await task
        scripture_cache[cache_key] = result
        return result
    except VerseNotFoundError as e:
        scripture_cache[cache_key] = e
        raise e
    finally:
        # Once the task is complete, remove it from the ongoing fetches.
        del ongoing_fetches[cache_key]

async def main():
    # Example usage to demonstrate async functionality with the new database backend
    print("--- Requesting multiple verses concurrently from the database ---")

    async def fetch_and_print(book, ref):
        try:
            text = await get_scripture_text(book, ref)
            print(f"\nSuccess for {book} {ref}:\n{text}")
        except VerseNotFoundError as e:
            print(f"\nError for {book} {ref}: {e}")

    # Create a list of tasks to run concurrently
    tasks = [
        fetch_and_print("John", "3:16"),
        fetch_and_print("Genesis", "1:1-3"),      # A range of verses
        fetch_and_print("John", "3:16"),          # This should be a cache hit
        fetch_and_print("NonExistentBook", "1:1"),# This should fail
        fetch_and_print("Psalms", "23:1-6"),      # Another range
    ]

    await asyncio.gather(*tasks)

if __name__ == '__main__':
    # Before running, ensure the database exists.
    import os
    if not os.path.exists("bible.db"):
        print("Database not found. Please run 'python database.py' to create it first.")
    else:
        asyncio.run(main())