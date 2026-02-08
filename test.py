import unittest
import asyncio
from scripture_finder import find_scripture_references, parse_and_expand_reference
from api_client import get_scripture_text, VerseNotFoundError, scripture_cache
import os

class TestScriptureFinder(unittest.TestCase):

    def test_simple_reference(self):
        self.assertEqual(find_scripture_references("Show me John 3:16"), [('John', '3:16')])

    def test_reference_with_range(self):
        self.assertEqual(find_scripture_references("1 Corinthians 13:4-7 is a good one"), [('1 Corinthians', '13:4-7')])

    def test_complex_reference_with_commas_and_ranges(self):
        self.assertEqual(find_scripture_references("Let's see Genesis 1:1-3,5,7-9"), [('Genesis', '1:1-3,5,7-9')])

    def test_multiple_complex_references(self):
        self.assertEqual(
            find_scripture_references("I like Genesis 1:1,3 and Romans 12:1-2,5"),
            [('Genesis', '1:1,3'), ('Romans', '12:1-2,5')]
        )

    def test_abbreviated_book(self):
        self.assertEqual(find_scripture_references("I like Psa 23:1"), [('Psa', '23:1')])

    def test_no_scripture(self):
        self.assertEqual(find_scripture_references("This is just a regular sentence."), [])

class TestParseAndExpandReference(unittest.TestCase):

    def test_single_verse(self):
        self.assertEqual(parse_and_expand_reference("3:16"), (3, [16]))

    def test_verse_range(self):
        self.assertEqual(parse_and_expand_reference("13:4-7"), (13, [4, 5, 6, 7]))

    def test_comma_separated_verses(self):
        self.assertEqual(parse_and_expand_reference("1:1,3,5"), (1, [1, 3, 5]))

    def test_mixed_ranges_and_commas(self):
        self.assertEqual(parse_and_expand_reference("1:1-3,5,8-10"), (1, [1, 2, 3, 5, 8, 9, 10]))

    def test_unordered_and_redundant(self):
        self.assertEqual(parse_and_expand_reference("1:5,1-2,5"), (1, [1, 2, 5]))

    def test_invalid_format(self):
        self.assertEqual(parse_and_expand_reference("invalid-string"), (None, []))

class TestApiClient(unittest.IsolatedAsyncioTestCase):

    @classmethod
    def setUpClass(cls):
        # Ensure the database exists before running tests
        if not os.path.exists("bible.db"):
            raise RuntimeError("Database file 'bible.db' not found. Please run 'python database.py' first.")

    def setUp(self):
        """Clear the cache before each test."""
        scripture_cache.clear()

    async def test_fetch_single_verse(self):
        """Test fetching a single, valid verse."""
        text = await get_scripture_text("John", "3:16")
        self.assertIn("For God so loved the world", text)

    async def test_fetch_verse_range(self):
        """Test fetching a range of verses."""
        text = await get_scripture_text("Genesis", "1:1-3")
        self.assertIn("In the beginning God created", text)
        self.assertIn("And the earth was without form", text)
        self.assertIn("And God said, Let there be light", text)

    async def test_caching_works(self):
        """Test that a previously fetched verse is served from cache."""
        # First call should be a miss and populate the cache
        await get_scripture_text("Romans", "8:28")
        self.assertIn("romans:8:28", scripture_cache)

        # To test if it's from the cache, we can check the console output or time it.
        # For this test, we'll just confirm the key exists.
        # A more advanced test could mock the database to ensure it's not called a second time.

        # Second call should be a hit
        text = await get_scripture_text("Romans", "8:28")
        self.assertIn("all things work together for good", text)

    async def test_verse_not_found_error(self):
        """Test that an invalid verse reference raises VerseNotFoundError."""
        with self.assertRaises(VerseNotFoundError):
            await get_scripture_text("Genesis", "99:99")

    async def test_error_caching(self):
        """Test that an error is cached to prevent repeated failed lookups."""
        # First call should raise an error and cache it
        with self.assertRaises(VerseNotFoundError):
            await get_scripture_text("Genesis", "1:99") # Invalid verse

        self.assertIn("genesis:1:99", scripture_cache)
        self.assertIsInstance(scripture_cache["genesis:1:99"], VerseNotFoundError)

        # Second call should also raise the error, but from the cache
        with self.assertRaises(VerseNotFoundError):
            await get_scripture_text("Genesis", "1:99")

if __name__ == '__main__':
    unittest.main()