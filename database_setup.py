import sqlite3

# --- Database Connection ---
# This script connects to an SQLite database file named 'bible.db'.
# If the file does not exist, SQLite will create it automatically.
db_connection = sqlite3.connect('bible.db')

# Create a cursor object. This object allows us to execute SQL commands.
cursor = db_connection.cursor()

# --- Table Creation ---
# This SQL statement defines the structure of the 'bible_verses' table.
# - id: A unique identifier for each verse (auto-incrementing integer).
# - book: The name of the Bible book (e.g., "Genesis").
# - chapter: The chapter number.
# - verse: The verse number.
# - text: The content of the verse.
# - translation: The Bible version (e.g., "KJV").
# The "IF NOT EXISTS" clause prevents an error if the table has already been created.
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

# Execute the SQL command to create the table.
cursor.execute(create_table_query)

# --- Commit and Close ---
# Commit the changes to the database. This saves the new table structure.
db_connection.commit()

# Close the database connection to free up resources.
db_connection.close()

print("Database 'bible.db' and table 'bible_verses' initialized successfully.")