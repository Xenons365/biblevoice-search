import asyncio
from scripture_finder import find_scripture_references
from data_manager import get_scripture_text, VerseNotFoundError

async def process_input(text):
    """
    Finds, fetches, and displays scripture references from a given text.
    """
    references = find_scripture_references(text)
    if not references:
        print("No scripture reference found. Please try again.\n")
        return

    # Create a list of tasks to fetch all verses concurrently
    tasks = [get_scripture_text(book.strip(), ref) for book, ref in references]

    # Use asyncio.gather with return_exceptions=True to handle potential errors
    results = await asyncio.gather(*tasks, return_exceptions=True)

    # Display all fetched verses or errors
    print("\n" + "="*50)
    for (book, ref), result in zip(references, results):
        book_title = book.strip().title()
        if isinstance(result, (VerseNotFoundError, FileNotFoundError)):
            print(f"Error: Could not find '{book_title} {ref}'.")
            print(f"  > {result}\n")
        elif isinstance(result, Exception):
            print(f"An unexpected error occurred for '{book_title} {ref}': {result}\n")
        else:
            print(f"Displaying: {book_title} {ref}")
            print("-" * 50)
            print(f"{result}\n")
    print("="*50)

async def start_cli():
    """
    Starts the asynchronous command-line interface.
    """
    print("Welcome to the Async Scripture Projector!")
    print("Type a sentence with scripture references (e.g., 'John 3:16 and Gen 1:1') or 'quit' to exit.\n")

    while True:
        try:
            user_input = await asyncio.to_thread(input, "> ")
            if user_input.lower() == "quit":
                break
            await process_input(user_input)
        except (KeyboardInterrupt, EOFError):
            print("\nExiting.")
            break