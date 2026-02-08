import re
import csv

# This list contains the exact titles as they appear in the Gutenberg text file.
BOOK_NAMES = [
    "The First Book of Moses: Called Genesis", "The Second Book of Moses: Called Exodus",
    "The Third Book of Moses: Called Leviticus", "The Fourth Book of of Moses: Called Numbers",
    "The Fifth Book of Moses: Called Deuteronomy", "The Book of Joshua", "The Book of Judges",
    "The Book of Ruth", "The First Book of Samuel", "The Second Book of Samuel",
    "The First Book of the Kings", "The Second Book of the Kings", "The First Book of the Chronicles",
    "The Second Book of the Chronicles", "The Book of Ezra", "The Book of Nehemiah",
    "The Book of Esther", "The Book of Job", "The Book of Psalms", "The Book of Proverbs",
    "The book of Ecclesiastes", "The Song of Solomon", "The Book of the Prophet Isaiah",
    "The Book of the Prophet Jeremiah", "The Lamentations of Jeremiah", "The Book of the Prophet Ezekiel",
    "The Book of the Prophet Daniel", "The Book of Hosea", "The Book of Joel", "The Book of Amos",
    "The Book of Obadiah", "The Book of Jonah", "The Book of Micah", "The Book of Nahum",
    "The Book of Habakkuk", "The Book of Zephaniah", "The Book of Haggai", "The Book of Zechariah",
    "The Book of Malachi", "The Gospel According to Saint Matthew", "The Gospel According to Saint Mark",
    "The Gospel According to Saint Luke", "The Gospel According to Saint John", "The Acts of the Apostles",
    "The Epistle of Paul the Apostle to the Romans", "The First Epistle of Paul the Apostle to the Corinthians",
    "The Second Epistle of Paul the Apostle to the Corinthians", "The Epistle of Paul the Apostle to the Galatians",
    "The Epistle of Paul the Apostle to the Ephesians", "The Epistle of Paul the Apostle to the Philippians",
    "The Epistle of Paul the Apostle to the Colossians", "The First Epistle of Paul the Apostle to the Thessalonians",
    "The Second Epistle of Paul the Apostle to the Thessalonians", "The First Epistle of Paul the Apostle to Timothy",
    "The Second Epistle of Paul the Apostle to Timothy", "The Epistle of Paul the Apostle to Titus",
    "The Epistle of Paul the Apostle to Philemon", "The Epistle of Paul the Apostle to the Hebrews",
    "The General Epistle of James", "The First Epistle General of Peter", "The Second Epistle General of Peter",
    "The First Epistle General of John", "The Second Epistle of John", "The Third Epistle of John",
    "The General Epistle of Jude", "The Revelation of St. John the Divine"
]

def get_standard_book_name(title):
    """
    Converts raw book titles from the Gutenberg text to the standard format.
    """
    title_map = {
        "The First Book of Moses: Called Genesis": "Genesis", "The Second Book of Moses: Called Exodus": "Exodus",
        "The Third Book of Moses: Called Leviticus": "Leviticus", "The Fourth Book of Moses: Called Numbers": "Numbers",
        "The Fifth Book of Moses: Called Deuteronomy": "Deuteronomy", "The Book of Joshua": "Joshua",
        "The Book of Judges": "Judges", "The Book of Ruth": "Ruth", "The First Book of Samuel": "1 Samuel",
        "The Second Book of Samuel": "2 Samuel", "The First Book of the Kings": "1 Kings",
        "The Second Book of the Kings": "2 Kings", "The First Book of the Chronicles": "1 Chronicles",
        "The Second Book of the Chronicles": "2 Chronicles", "The Book of Ezra": "Ezra",
        "The Book of Nehemiah": "Nehemiah", "The Book of Esther": "Esther", "The Book of Job": "Job",
        "The Book of Psalms": "Psalms", "The Book of Proverbs": "Proverbs", "The book of Ecclesiastes": "Ecclesiastes",
        "The Song of Solomon": "Song of Solomon", "The Book of the Prophet Isaiah": "Isaiah",
        "The Book of the Prophet Jeremiah": "Jeremiah", "The Lamentations of Jeremiah": "Lamentations",
        "The Book of the Prophet Ezekiel": "Ezekiel", "The Book of the Prophet Daniel": "Daniel",
        "The Book of Hosea": "Hosea", "The Book of Joel": "Joel", "The Book of Amos": "Amos",
        "The Book of Obadiah": "Obadiah", "The Book of Jonah": "Jonah", "The Book of Micah": "Micah",
        "The Book of Nahum": "Nahum", "The Book of Habakkuk": "Habakkuk", "The Book of Zephaniah": "Zephaniah",
        "The Book of Haggai": "Haggai", "The Book of Zechariah": "Zechariah", "The Book of Malachi": "Malachi",
        "The Gospel According to Saint Matthew": "Matthew", "The Gospel According to Saint Mark": "Mark",
        "The Gospel According to Saint Luke": "Luke", "The Gospel According to Saint John": "John",
        "The Acts of the Apostles": "Acts", "The Epistle of Paul the Apostle to the Romans": "Romans",
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
        "The Epistle of Paul the Apostle to Titus": "Titus", "The Epistle of Paul the Apostle to Philemon": "Philemon",
        "The Epistle of Paul the Apostle to the Hebrews": "Hebrews", "The General Epistle of James": "James",
        "The First Epistle General of Peter": "1 Peter", "The Second Epistle General of Peter": "2 Peter",
        "The First Epistle General of John": "1 John", "The Second Epistle of John": "2 John",
        "The Third Epistle of John": "3 John", "The General Epistle of Jude": "Jude",
        "The Revelation of St. John the Divine": "Revelation"
    }
    return title_map.get(title, title)

def parse_bible_to_csv(input_file, output_file):
    """
    Parses a plain text file of the KJV Bible and converts it into a CSV file.
    """
    verse_pattern = re.compile(r'(\d{1,3}:\d{1,3})\s(.+)')
    current_book = ""
    parsing_started = False

    with open(input_file, 'r', encoding='utf-8') as infile, \
         open(output_file, 'w', newline='', encoding='utf-8') as outfile:

        csv_writer = csv.writer(outfile)
        csv_writer.writerow(['book', 'chapter', 'verse', 'text', 'translation'])

        book_name_set = set(BOOK_NAMES)

        for line in infile:
            stripped_line = line.strip()

            if not parsing_started:
                if stripped_line == "The First Book of Moses: Called Genesis":
                    parsing_started = True
                    current_book = get_standard_book_name(stripped_line)
                continue

            if not stripped_line:
                continue

            if stripped_line in book_name_set:
                current_book = get_standard_book_name(stripped_line)
                continue

            match = verse_pattern.match(stripped_line)
            if match and current_book:
                reference, text = match.groups()
                chapter, verse = reference.split(':')

                csv_writer.writerow([current_book, chapter, verse, text.strip(), "KJV"])

if __name__ == '__main__':
    print("Parsing KJV Bible text file to CSV...")
    parse_bible_to_csv('kjv_bible.txt', 'kjv_bible.csv')
    print("Parsing complete. Output saved to 'kjv_bible.csv'.")