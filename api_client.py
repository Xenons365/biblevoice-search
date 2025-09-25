import time

def get_scripture_text(book, reference):
    """
    Mocks a call to a Bible API.

    In a real application, this function would make an HTTP request
    to a Bible API to get the text of the scripture.

    For now, it returns a placeholder text after a short delay.
    """
    print(f"Fetching {book} {reference} from API...")
    time.sleep(1)  # Simulate network delay

    # Mocked response
    mock_text = f'"{book} {reference}" - This is the mock text for the scripture. In a real application, this would be the actual verse from the Bible.'

    return mock_text

if __name__ == '__main__':
    # Example usage:
    book = "John"
    reference = "3:16"
    text = get_scripture_text(book, reference)
    print("API Response:")
    print(text)

    book = "1 Corinthians"
    reference = "13:4-7"
    text = get_scripture_text(book, reference)
    print("\nAPI Response:")
    print(text)