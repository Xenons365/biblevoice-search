import sqlite3
import csv

def create_database(db_name, csv_file):
    """
    Creates an SQLite database and populates it with data from a CSV file.

    The function creates a 'verses' table and inserts the book, chapter,
    verse, text, and translation for each record in the CSV.
    """
    conn = sqlite3.connect(db_name)
    c = conn.cursor()

    # Create table
    c.execute('''
        CREATE TABLE IF NOT EXISTS verses (
            id INTEGER PRIMARY KEY,
            book TEXT NOT NULL,
            chapter INTEGER NOT NULL,
            verse INTEGER NOT NULL,
            text TEXT NOT NULL,
            translation TEXT NOT NULL
        )
    ''')

    # Create an index for faster queries
    c.execute('CREATE INDEX IF NOT EXISTS idx_verses_book_chapter_verse ON verses (book, chapter, verse)')

    # Load data from CSV
    with open(csv_file, 'r', encoding='utf-8') as f:
        reader = csv.reader(f)
        next(reader)  # Skip header row
        for row in reader:
            c.execute(
                "INSERT INTO verses (book, chapter, verse, text, translation) VALUES (?, ?, ?, ?, ?)",
                (row[0], row[1], row[2], row[3], row[4])
            )

    conn.commit()
    conn.close()
    print(f"Database '{db_name}' created and populated successfully.")

if __name__ == '__main__':
    create_database('kjv_bible.db', 'kjv_bible.csv')