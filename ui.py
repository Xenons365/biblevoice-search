from scripture_finder import find_scripture_references
from api_client import get_scripture_text

def start_cli():
    """
    Starts the command-line interface for the scripture projector.
    """
    print("Welcome to the Scripture Projector!")
    print("Type a sentence containing a scripture reference (e.g., 'Show me John 3:16') or 'quit' to exit.")

    while True:
        user_input = input("> ")
        if user_input.lower() == 'quit':
            break

        references = find_scripture_references(user_input)

        if not references:
            print("No scripture reference found. Please try again.")
            continue

        for book, reference in references:
            # For now, we just fetch and print the first one found.
            # In the future, we could handle multiple references.
            scripture_text = get_scripture_text(book.strip(), reference)

            # Simple formatting for projection
            print("\n" + "="*50)
            print(f"Displaying: {book.strip().title()} {reference}")
            print("="*50)
            print(f"\n{scripture_text}\n")
            print("="*50)
            break # Only handling the first found reference for now