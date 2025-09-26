import asyncio

# Custom exception for API errors
class VerseNotFoundError(Exception):
    pass

# In-memory cache for scripture texts
scripture_cache = {}
# Dictionary to track in-flight requests to prevent race conditions
ongoing_fetches = {}

async def _fetch_from_api(book, reference):
    """The internal function that performs the actual fetch."""
    print(f"Cache miss. Fetching {book} {reference} from API...")
    await asyncio.sleep(1)  # Simulate non-blocking network delay

    if "99" in reference:
        print(f"API error: Verse {book} {reference} not found.")
        raise VerseNotFoundError(f"The verse '{book} {reference}' could not be found.")

    return f'"{book} {reference}" - This is the mock text for the scripture.'

async def get_scripture_text(book, reference):
    """
    Asynchronously gets scripture text, with caching, error handling,
    and protection against race conditions.
    """
    cache_key = f"{book.lower()}:{reference}"

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
    task = asyncio.create_task(_fetch_from_api(book, reference))
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
    # Example usage to demonstrate async functionality:
    print("--- Requesting multiple verses concurrently ---")

    async def fetch_and_print(book, ref):
        try:
            text = await get_scripture_text(book, ref)
            print(f"Success for {book} {ref}: {text}")
        except VerseNotFoundError as e:
            print(f"Error for {book} {ref}: {e}")

    tasks = [
        fetch_and_print("John", "3:16"),
        fetch_and_print("Genesis", "1:99"),
        fetch_and_print("John", "3:16"), # This should now wait for the first fetch
    ]

    await asyncio.gather(*tasks)

if __name__ == '__main__':
    asyncio.run(main())