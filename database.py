import sqlite3
import re
import os

DATABASE_FILE = "bible.db"
BIBLE_TEXT_FILE = "kjv.txt"

# This dictionary maps the exact titles from the Gutenberg file to our canonical book names.
BOOK_TITLE_MAP = {
    "The First Book of Moses: Called Genesis": "Genesis",
    "The Second Book of Moses: Called Exodus": "Exodus",
    "The Third Book of Moses: Called Leviticus": "Leviticus",
    "The Fourth Book of Moses: Called Numbers": "Numbers",
    "The Fifth Book of Moses: Called Deuteronomy": "Deuteronomy",
    "The Book of Joshua": "Joshua",
    "The Book of Judges": "Judges",
    "The Book of Ruth": "Ruth",
    "The First Book of Samuel": "1 Samuel",
    "The Second Book of Samuel": "2 Samuel",
    "The First Book of the Kings": "1 Kings",
    "The Second Book of the Kings": "2 Kings",
    "The First Book of the Chronicles": "1 Chronicles",
    "The Second Book of the Chronicles": "2 Chronicles",
    "Ezra": "Ezra",
    "The Book of Nehemiah": "Nehemiah",
    "The Book of Esther": "Esther",
    "The Book of Job": "Job",
    "The Book of Psalms": "Psalms",
    "The Proverbs": "Proverbs",
    "Ecclesiastes": "Ecclesiastes",
    "The Song of Solomon": "Song of Solomon",
    "The Book of the Prophet Isaiah": "Isaiah",
    "The Book of the Prophet Jeremiah": "Jeremiah",
    "The Lamentations of Jeremiah": "Lamentations",
    "The Book of the Prophet Ezekiel": "Ezekiel",
    "The Book of Daniel": "Daniel",
    "Hosea": "Hosea",
    "Joel": "Joel",
    "Amos": "Amos",
    "Obadiah": "Obadiah",
    "Jonah": "Jonah",
    "Micah": "Micah",
    "Nahum": "Nahum",
    "Habakkuk": "Habakkuk",
    "Zephaniah": "Zephaniah",
    "Haggai": "Haggai",
    "Zechariah": "Zechariah",
    "Malachi": "Malachi",
    "The Gospel According to Saint Matthew": "Matthew",
    "The Gospel According to Saint Mark": "Mark",
    "The Gospel According to Saint Luke": "Luke",
    "The Gospel According to Saint John": "John",
    "The Acts of the Apostles": "Acts",
    "The Epistle of Paul the Apostle to the Romans": "Romans",
    "The First Epistle of Paul the Apostle to the Corinthians": "1 Corinthians",
    "The Second Epistle of Paul the Apostle to the Corinthians": "2 Corinthians",
    "The Epistle of Paul the Apostle to the Galatians": "Galatians",
    "The Epistle of Paul the Apostle to the Ephesians": "Ephesians",
    "The Epistle of Paul the Apostle to the Philippians": "Philippians",
    "The Epistle of Paul the Apostle to the Colossians": "Colossians",
    "The First Epistle of Paul the Apostle to the Thessalonians": "1 Thessalonians",
    "The Second Epistle of Paul the Apostle to the Thessalonians": "2 Thessalonians",
    "The First Epistle of Paul the Apostle to Timothy": "1 Timothy",
    "The Second Epistle of Paul the Apostle to Timothy": "2 Timothy",
    "The Epistle of Paul the Apostle to Titus": "Titus",
    "The Epistle of Paul the Apostle to Philemon": "Philemon",
    "The Epistle of Paul the Apostle to the Hebrews": "Hebrews",
    "The General Epistle of James": "James",
    "The First Epistle General of Peter": "1 Peter",
    "The Second General Epistle of Peter": "2 Peter",
    "The First Epistle General of John": "1 John",
    "The Second Epistle General of John": "2 John",
    "The Third Epistle General of John": "3 John",
    "The General Epistle of Jude": "Jude",
    "The Revelation of Saint John the Divine": "Revelation",
}

def create_database(force_create=False):
    if os.path.exists(DATABASE_FILE) and not force_create:
        print("Database already exists. Skipping creation.")
        return

    if os.path.exists(DATABASE_FILE):
        os.remove(DATABASE_FILE)

    conn = sqlite3.connect(DATABASE_FILE)
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE bible_verses (
            id INTEGER PRIMARY KEY,
            book TEXT NOT NULL,
            chapter INTEGER NOT NULL,
            verse INTEGER NOT NULL,
            text TEXT NOT NULL,
            UNIQUE(book, chapter, verse)
        )
    """)

    print("Database created. Populating with scripture...")

    with open(BIBLE_TEXT_FILE, "r", encoding="utf-8") as f:
        lines = f.readlines()

    current_book = None
    total_verses = 0
    parsing_active = False

    verse_marker_regex = re.compile(r'(\d+:\d+)\s')

    for line in lines:
        line = line.strip()

        # The content we want to parse is between the START and END markers.
        if "*** START OF THE PROJECT GUTENBERG EBOOK 10 ***" in line:
            parsing_active = True
            continue
        if "*** END OF THE PROJECT GUTENBERG EBOOK 10 ***" in line:
            break

        if not parsing_active or not line:
            continue

        # Check if the line is a book title.
        if line in BOOK_TITLE_MAP:
            current_book = BOOK_TITLE_MAP[line]
            print(f"--- Parsing book: {current_book} ---")
            continue

        if current_book:
            # Split the line by verse markers to handle multiple verses per line.
            parts = verse_marker_regex.split(line)
            i = 1
            while i < len(parts):
                try:
                    marker = parts[i]
                    text = parts[i+1].strip()

                    chapter_str, verse_str = marker.split(':')
                    chapter = int(chapter_str)
                    verse_num = int(verse_str)

                    cursor.execute(
                        "INSERT OR IGNORE INTO bible_verses (book, chapter, verse, text) VALUES (?, ?, ?, ?)",
                        (current_book, chapter, verse_num, text)
                    )
                    if cursor.rowcount > 0:
                        total_verses += 1
                except (ValueError, IndexError):
                    pass # Ignore parts that don't conform to the expected format
                i += 2

    conn.commit()
    conn.close()
    print(f"\nDatabase population complete. Inserted {total_verses} verses.")


def get_verse(book, chapter, verse):
    conn = sqlite3.connect(DATABASE_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT text FROM bible_verses WHERE book=? AND chapter=? AND verse=?", (book, chapter, verse))
    result = cursor.fetchone()
    conn.close()
    return result[0] if result else f"Verse {book} {chapter}:{verse} not found."

def get_verses_in_range(book, chapter, start_verse, end_verse):
    conn = sqlite3.connect(DATABASE_FILE)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT text FROM bible_verses
        WHERE book=? AND chapter=? AND verse BETWEEN ? AND ?
        ORDER BY verse
    """, (book, chapter, start_verse, end_verse))
    results = cursor.fetchall()
    conn.close()
    return [row[0] for row in results]

if __name__ == "__main__":
    create_database(force_create=True)

    print("\n--- Verifying database content ---")
    print("Fetching Genesis 1:1...")
    verse_text = get_verse("Genesis", 1, 1)
    print(f"  -> {verse_text}")

    print("\nFetching John 3:16...")
    verse_text = get_verse("John", 3, 16)
    print(f"  -> {verse_text}")

    print("\nFetching Revelation 22:21...")
    verse_text = get_verse("Revelation", 22, 21)
    print(f"  -> {verse_text}")