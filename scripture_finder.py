import re

BIBLE_BOOKS = {
    "Genesis": ["Gen", "Ge", "Gn"],
    "Exodus": ["Ex", "Exo", "Exod"],
    "Leviticus": ["Lev", "Le", "Lv"],
    "Numbers": ["Num", "Nu", "Nm", "Nb"],
    "Deuteronomy": ["Deut", "Dt"],
    "Joshua": ["Josh", "Jos", "Jsh"],
    "Judges": ["Judg", "Jdg", "Jg", "Jdgs"],
    "Ruth": ["Rth", "Ru"],
    "1 Samuel": ["1 Sam", "1 Sa", "1 S", "I Sa", "1 Sm", "1Sa", "ISa", "1S", "IS", "1Samuel"],
    "2 Samuel": ["2 Sam", "2 Sa", "2 S", "II Sa", "2 Sm", "2Sa", "IISa", "2S", "IIS", "2Samuel"],
    "1 Kings": ["1 Kgs", "1 Ki", "1K", "IK", "1Kin", "1Kgs", "IKgs", "1kin"],
    "2 Kings": ["2 Kgs", "2 Ki", "2K", "IIK", "2Kin", "2Kgs", "IIKgs", "2kin"],
    "1 Chronicles": ["1 Chr", "1 Ch", "I Ch", "1Chr", "IChr", "1ch"],
    "2 Chronicles": ["2 Chr", "2 Ch", "II Ch", "2Chr", "IIChr", "2ch"],
    "Ezra": ["Ezr", "Ez"],
    "Nehemiah": ["Neh", "Ne"],
    "Esther": ["Esth", "Es"],
    "Job": ["Jb"],
    "Psalms": ["Ps", "Psalm", "Pslm", "Psa"],
    "Proverbs": ["Prov", "Pro", "Prv"],
    "Ecclesiastes": ["Eccles", "Eccle", "Eccl", "Ecc", "Qoh"],
    "Song of Solomon": ["Song", "So", "SOS"],
    "Isaiah": ["Isa", "Is"],
    "Jeremiah": ["Jer", "Je", "Jr"],
    "Lamentations": ["Lam", "La"],
    "Ezekiel": ["Ezek", "Eze", "Ezk"],
    "Daniel": ["Dan", "Da", "Dn"],
    "Hosea": ["Hos", "Ho"],
    "Joel": ["Jl"],
    "Amos": ["Am"],
    "Obadiah": ["Obad", "Ob"],
    "Jonah": ["Jon", "Jnh"],
    "Micah": ["Mic"],
    "Nahum": ["Nah", "Na"],
    "Habakkuk": ["Hab"],
    "Zephaniah": ["Zeph", "Zep", "Zp"],
    "Haggai": ["Hag", "Hg"],
    "Zechariah": ["Zech", "Zec", "Zc"],
    "Malachi": ["Mal", "Ml"],
    "Matthew": ["Matt", "Mt"],
    "Mark": ["Mrk", "Mar", "Mk"],
    "Luke": ["Luk", "Lk"],
    "John": ["Jhn", "Jn"],
    "Acts": ["Act", "Ac"],
    "Romans": ["Rom", "Ro", "Rm"],
    "1 Corinthians": ["1 Cor", "1 Co", "I Co", "1Co", "ICo", "1Corinthians"],
    "2 Corinthians": ["2 Cor", "2 Co", "II Co", "2Co", "IICo", "2Corinthians"],
    "Galatians": ["Gal", "Ga"],
    "Ephesians": ["Eph", "Ephes"],
    "Philippians": ["Phil", "Php", "Pp"],
    "Colossians": ["Col"],
    "1 Thessalonians": ["1 Thess", "1 Th", "I Th", "1Th", "ITh", "1Thessalonians"],
    "2 Thessalonians": ["2 Thess", "2 Th", "II Th", "2Th", "IITh", "2Thessalonians"],
    "1 Timothy": ["1 Tim", "1 Ti", "I Ti", "1Ti", "ITi", "1Timothy"],
    "2 Timothy": ["2 Tim", "2 Ti", "II Ti", "2Ti", "IITi", "2Timothy"],
    "Titus": ["Tit", "Ti"],
    "Philemon": ["Philem", "Phm", "Pm"],
    "Hebrews": ["Heb"],
    "James": ["Jas", "Jm"],
    "1 Peter": ["1 Pet", "1 Pe", "I Pe", "1Pe", "IPe", "1Peter"],
    "2 Peter": ["2 Pet", "2 Pe", "II Pe", "2Pe", "IIPe", "2Peter"],
    "1 John": ["1 John", "1 Jn", "I Jn", "1Jn", "IJn", "1John"],
    "2 John": ["2 John", "2 Jn", "II Jn", "2Jn", "IIJn", "2John"],
    "3 John": ["3 John", "3 Jn", "III Jn", "3Jn", "IIIJn", "3John"],
    "Jude": ["Jud"],
    "Revelation": ["Rev", "Re", "The Revelation"],
}

def find_scripture_references(text):
    """
    Finds scripture references in a given text.
    """
    all_books = []
    for book, abbrevs in BIBLE_BOOKS.items():
        all_books.append(book)
        all_books.extend(abbrevs)

    # Regex to match scripture references
    # It looks for:
    # - Optional number (e.g., 1, 2, 3)
    # - Book name (including abbreviations)
    # - Chapter and verse (e.g., 1:1, 1:1-2, 1:1,3)
    book_regex = r"(\d?\s?)?(" + "|".join(all_books) + r")"
    verse_regex = r"(\d+:\d+(-\d+)?(,\s?\d+)*)"
    # The regex needs to be constructed carefully to avoid capturing parts of the book names as separate groups.
    # The current regex has too many capturing groups, which makes the output of findall hard to parse.
    # Let's simplify the regex and the find_scripture_references function.

    # Create a single regex for all book names and their abbreviations.
    book_names_regex = []
    for book, abbrevs in BIBLE_BOOKS.items():
        # Handle books that start with a number (e.g., "1 Samuel", "2 Kings").
        if book[0].isdigit():
            num = book[0]
            name = book[2:]

            # Add regex variations for the number to match "1", "1st", etc.
            # The `(?:...)` is a non-capturing group.
            book_names_regex.append(f"{num}(?:st|nd|rd|th)?\\s?{name}")
            for abbrev in abbrevs:
                 # Also apply the same logic to abbreviations of numbered books.
                 book_names_regex.append(f"{abbrev.replace('1', '1(?:st)?').replace('2', '2(?:nd)?').replace('3', '3(?:rd)?')}")
        else:
            # For non-numbered books, just add the book name and its abbreviations.
            book_names_regex.append(book)
            book_names_regex.extend(abbrevs)

    # Sort the list of book names by length in descending order.
    # This is crucial to ensure the regex engine matches longer names first
    # (e.g., "1 John" before "John").
    book_names_regex.sort(key=len, reverse=True)

    # Join all book names and abbreviations into a single regex pattern
    books_pattern = "|".join(book_names_regex)

    # Regex to capture the full scripture reference.
    # It looks for a book name, followed by a complex chapter and verse pattern.
    # Example: "John 3:16", "1 Corinthians 13:4-7", "Genesis 1:1,3-5"
    verse_pattern = r"(\d{1,3}:\d{1,3}(?:-\d{1,3})?(?:,\s*\d{1,3}(?:-\d{1,3})?)*)"
    scripture_pattern = re.compile(
        r"\b(" + books_pattern + r")\s+" + verse_pattern + r"\b",
        re.IGNORECASE
    )

    return scripture_pattern.findall(text)

# Example usage and testing:
if __name__ == '__main__':
    test_strings = [
        "Please show me John 3:16.",
        "I like the verse 1 Corinthians 13:4-7, it is very inspiring.",
        "Let's look at Genesis 1:1.",
        "Can you find Psa 23:1 for me?",
        "Show me 1st samuel 1:1",
        "The verse is from 2 Tim 2:15",
        "No scripture here.",
        "This is a test for Rev 22:20-21",
        "I need to see romans 8:28",
        "Let's check Genesis 1:1,3-5 and John 3:16"
    ]

    for s in test_strings:
        found = find_scripture_references(s)
        if found:
            print(f"In '{s}', found: {found}")
        else:
            print(f"In '{s}', no scripture found.")