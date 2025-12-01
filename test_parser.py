import unittest
import os
import sqlite3
from parse_and_import import setup_and_import

class TestParser(unittest.TestCase):

    def setUp(self):
        """Set up a temporary environment for testing."""
        # Define paths for a temporary database and a temporary CSV file.
        self.db_path = 'test_bible.db'
        self.csv_path = 'test_verses.csv'

        # Create a dummy CSV file with sample data for the test.
        with open(self.csv_path, 'w', newline='', encoding='utf-8') as f:
            f.write("book,chapter,verse,text,translation\n")
            f.write('TestBook,1,1,"This is a test verse.","TEST"\n')
            f.write('TestBook,1,2,"This is another test verse.","TEST"\n')

    def tearDown(self):
        """Clean up the temporary files after each test."""
        if os.path.exists(self.db_path):
            os.remove(self.db_path)
        if os.path.exists(self.csv_path):
            os.remove(self.csv_path)

    def test_import_process(self):
        """
        Test the entire setup and import process from start to finish.
        """
        # --- 1. Run the import function ---
        setup_and_import(self.db_path, self.csv_path)

        # --- 2. Verify the database file was created ---
        self.assertTrue(os.path.exists(self.db_path), "Database file should be created.")

        # --- 3. Connect to the new database and verify its contents ---
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Check if the table was created
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='bible_verses';")
        self.assertIsNotNone(cursor.fetchone(), "The 'bible_verses' table should exist.")

        # Check if the correct number of rows were imported
        cursor.execute("SELECT COUNT(*) FROM bible_verses;")
        count = cursor.fetchone()[0]
        self.assertEqual(count, 2, "Should have imported exactly 2 verses.")

        # Check the content of a specific verse to ensure correctness
        cursor.execute("SELECT book, chapter, verse, text, translation FROM bible_verses WHERE verse = 2;")
        row = cursor.fetchone()
        self.assertIsNotNone(row, "Verse 2 should exist.")
        self.assertEqual(row, ('TestBook', 1, 2, 'This is another test verse.', 'TEST'))

        conn.close()

if __name__ == '__main__':
    unittest.main()