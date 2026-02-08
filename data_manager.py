import asyncio
import sqlite3
import os

# Custom exception for DB errors
class VerseNotFoundError(Exception):
    pass

# In-memory cache for scripture texts
scripture_cache = {}
# Dictionary to track in-flight requests to prevent race conditions
ongoing_fetches = {}
DB_PATH = 'kjv_bible.db'

def _query_db(book, chapter, start_verse, end_verse=None, translation='KJV'):
    """
    Synchronously queries the database for one or more verses.
    This function is intended to be run in a separate thread.
    """
    if not os.path.exists(DB_PATH):
        raise FileNotFoundError(f"Database file not found at '{DB_PATH}'. Please run database_setup.py.")

    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    if end_verse:
        # Query for a range of verses
        c.execute(
            """
            SELECT verse, text FROM verses
            WHERE book = ? AND chapter = ? AND verse >= ? AND verse <= ? AND translation = ?
            ORDER BY verse ASC
            """,
            (book, chapter, start_verse, end_verse, translation)
        )
    else:
        # Query for a single verse
        c.execute(
            "SELECT verse, text FROM verses WHERE book = ? AND chapter = ? AND verse = ? AND translation = ?",
            (book, chapter, start_verse, translation)
        )

    results = c.fetchall()
    conn.close()

    if not results:
        ref_str = f"{chapter}:{start_verse}-{end_verse}" if end_verse else f"{chapter}:{start_verse}"
        raise VerseNotFoundError(f"The verse '{book} {ref_str}' could not be found for translation '{translation}'.")

    # Format the results into a single string
    return "\n".join([f"{verse_num} {text}" for verse_num, text in results])


async def get_scripture_text(book, reference, translation='KJV'):
    """
    Asynchronously gets scripture text from the SQLite database, with caching and race condition protection.
    Handles single verses (e.g., "3:16") and ranges (e.g., "3:16-18").
    """
    # Standardize the cache key to be lowercase
    cache_key = f"{translation.lower()}:{book.lower()}:{reference}"

    # Check cache first
    if cache_key in scripture_cache:
        print(f"Cache hit for {book} {reference} ({translation}).")
        cached_value = scripture_cache[cache_key]
        if isinstance(cached_value, Exception):
            raise cached_value
        return cached_value

    # Check for ongoing fetches to prevent race conditions
    if cache_key in ongoing_fetches:
        print(f"Waiting for existing DB query for {book} {reference} ({translation})...")
        return await ongoing_fetches[cache_key]

    # No cache hit and no ongoing fetch, so create a new one.
    try:
        # Parse chapter and verse(s) from the reference string
        chapter_str, verse_str = reference.split(':')
        chapter = int(chapter_str)

        if '-' in verse_str:
            start_verse_str, end_verse_str = verse_str.split('-')
            start_verse = int(start_verse_str)
            end_verse = int(end_verse_str)
        else:
            start_verse = int(verse_str)
            end_verse = None

        # Create a new task for the database query
        task = asyncio.create_task(
            asyncio.to_thread(_query_db, book, chapter, start_verse, end_verse, translation)
        )
        ongoing_fetches[cache_key] = task
        print(f"Cache miss. Querying DB for {book} {reference} ({translation})...")

        result = await task
        scripture_cache[cache_key] = result # Cache the successful result
        return result

    except (VerseNotFoundError, FileNotFoundError) as e:
        scripture_cache[cache_key] = e # Cache the exception
        raise e
    except Exception as e:
        err = VerseNotFoundError(f"Invalid reference format for '{book} {reference}': {e}")
        scripture_cache[cache_key] = err
        raise err
    finally:
        # Once the task is complete, remove it from the ongoing fetches.
        if cache_key in ongoing_fetches:
            del ongoing_fetches[cache_key]


async def main():
    """Example usage to demonstrate async functionality and race condition handling."""
    print("--- Requesting multiple verses concurrently from the database ---")

    async def fetch_and_print(book, ref, trans='KJV'):
        try:
            text = await get_scripture_text(book, ref, trans)
            print(f"Success for {book} {ref} ({trans}):\n{text}\n")
        except (VerseNotFoundError, FileNotFoundError) as e:
            print(f"Error for {book} {ref} ({trans}): {e}\n")

    tasks = [
        fetch_and_print("John", "3:16"),
        fetch_and_print("John", "3:16"),  # This should now wait for the first fetch
        fetch_and_print("Genesis", "1:1-3"),
        fetch_and_print("John", "3:99"),  # This should fail
    ]

    await asyncio.gather(*tasks)

if __name__ == '__main__':
    if not os.path.exists(DB_PATH):
        print(f"Error: Database not found at '{DB_PATH}'.")
        print("Please run 'python database_setup.py' first.")
    else:
        asyncio.run(main())