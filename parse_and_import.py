import sqlite3
import csv
import argparse
import os

def setup_and_import(db_path, csv_path):
    """
    Sets up the database schema and imports verses from a CSV file.
    This function will overwrite any existing data in the table.

    Args:
        db_path (str): The path to the SQLite database file.
        csv_path (str): The path to the CSV file containing the verses.
    """
    # --- 1. Database Connection ---
    try:
        # Connect to the SQLite database. If it doesn't exist, it will be created.
        db_connection = sqlite3.connect(db_path)
        cursor = db_connection.cursor()
    except sqlite3.Error as e:
        print(f"Database error: {e}")
        return

    try:
        # --- 2. Create Table ---
        # Define the table schema. "IF NOT EXISTS" is used for safety.
        create_table_query = """
        CREATE TABLE IF NOT EXISTS bible_verses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            book TEXT NOT NULL,
            chapter INTEGER NOT NULL,
            verse INTEGER NOT NULL,
            text TEXT NOT NULL,
            translation TEXT NOT NULL
        );
        """
        cursor.execute(create_table_query)

        # --- 3. Clear Existing Data ---
        # Delete all rows from the table to ensure a fresh import.
        cursor.execute("DELETE FROM bible_verses;")
        print(f"Cleared existing data from 'bible_verses' table in '{db_path}'.")

        # --- 4. Read CSV and Prepare Data ---
        with open(csv_path, mode='r', encoding='utf-8') as csv_file:
            csv_reader = csv.DictReader(csv_file)
            verses_to_insert = [
                (row['book'], row['chapter'], row['verse'], row['text'], row['translation'])
                for row in csv_reader
            ]

        # --- 5. Bulk Insert Data ---
        insert_query = """
        INSERT INTO bible_verses (book, chapter, verse, text, translation)
        VALUES (?, ?, ?, ?, ?);
        """
        cursor.executemany(insert_query, verses_to_insert)

        # --- 6. Commit and Report ---
        db_connection.commit()
        print(f"Successfully imported {cursor.rowcount} verses from '{csv_path}' into '{db_path}'.")

    except FileNotFoundError:
        print(f"Error: The file '{csv_path}' was not found.")
    except (csv.Error, KeyError) as e:
        print(f"CSV Error: Please ensure '{csv_path}' is a valid CSV with headers: book, chapter, verse, text, translation. Details: {e}")
        db_connection.rollback()
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        # Roll back any changes if an error occurs during the transaction.
        db_connection.rollback()
    finally:
        # --- 7. Close Connection ---
        db_connection.close()

if __name__ == '__main__':
    # --- Argument Parsing ---
    # Set up a command-line argument parser to get the input CSV file.
    parser = argparse.ArgumentParser(
        description="Bible Verse Parser & Importer.",
        formatter_class=argparse.RawTextHelpFormatter
    )
    parser.add_argument(
        'csv_file',
        type=str,
        help="Path to the Bible CSV file to import.\nThe CSV must have the following columns:\n  - book\n  - chapter\n  - verse\n  - text\n  - translation"
    )
    parser.add_argument(
        '--db-path',
        type=str,
        default='bible.db',
        help="Path to the SQLite database file (default: bible.db)."
    )

    args = parser.parse_args()

    # Check if the provided CSV file exists before proceeding.
    if not os.path.exists(args.csv_file):
        print(f"Error: Input file not found at '{args.csv_file}'")
    else:
        # Run the main setup and import function.
        setup_and_import(args.db_path, args.csv_file)