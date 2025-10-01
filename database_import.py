import sqlite3
import csv
import argparse

def import_verses_from_csv(db_path, csv_path):
    """
    Imports Bible verses from a CSV file into the SQLite database.

    Args:
        db_path (str): The path to the SQLite database file.
        csv_path (str): The path to the CSV file containing the verses.
    """
    # --- Database Connection ---
    # Connect to the specified SQLite database.
    try:
        db_connection = sqlite3.connect(db_path)
        cursor = db_connection.cursor()
    except sqlite3.Error as e:
        print(f"Database connection error: {e}")
        return

    # --- CSV Reading and Data Insertion ---
    try:
        # Open the CSV file with UTF-8 encoding.
        with open(csv_path, mode='r', encoding='utf-8') as csv_file:
            # Create a CSV reader object that treats the first row as headers.
            csv_reader = csv.DictReader(csv_file)

            verses_to_insert = []
            for row in csv_reader:
                # Prepare a tuple with the data for insertion.
                # The order must match the columns in the INSERT statement.
                verse_data = (
                    row['book'],
                    row['chapter'],
                    row['verse'],
                    row['text'],
                    row['translation']
                )
                verses_to_insert.append(verse_data)

            # --- Bulk Insertion ---
            # This SQL statement inserts a new row into the 'bible_verses' table.
            # The '?' are placeholders for the data we will provide.
            insert_query = """
            INSERT INTO bible_verses (book, chapter, verse, text, translation)
            VALUES (?, ?, ?, ?, ?);
            """

            # Use executemany for an efficient bulk insert.
            # This is much faster than inserting one row at a time.
            cursor.executemany(insert_query, verses_to_insert)

            # Commit the transaction to save all the inserted rows.
            db_connection.commit()

            # Print the number of verses that were successfully imported.
            print(f"Successfully imported {cursor.rowcount} verses from '{csv_path}'.")

    except FileNotFoundError:
        print(f"Error: The file '{csv_path}' was not found.")
    except Exception as e:
        print(f"An error occurred during CSV import: {e}")
        # If an error occurs, roll back any changes made during the transaction.
        db_connection.rollback()
    finally:
        # --- Close Connection ---
        # Always close the database connection when done.
        db_connection.close()

if __name__ == '__main__':
    # --- Argument Parsing ---
    # Set up an argument parser to handle command-line inputs.
    parser = argparse.ArgumentParser(description='Import Bible verses from a CSV file into a SQLite database.')

    # Define the command-line arguments.
    # - 'csv_path': The path to the CSV file (required).
    # - '--db-path': The path to the database file (optional, with a default value).
    parser.add_argument('csv_path', help='The path to the CSV file containing the verses.')
    parser.add_argument('--db-path', default='bible.db', help='The path to the SQLite database file (default: bible.db).')

    # Parse the arguments provided by the user.
    args = parser.parse_args()

    # Call the import function with the parsed arguments.
    import_verses_from_csv(args.db_path, args.csv_path)