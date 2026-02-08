import unittest
import asyncio
from scripture_finder import find_scripture_references
from data_manager import get_scripture_text, VerseNotFoundError, scripture_cache, ongoing_fetches

class TestScriptureFinder(unittest.TestCase):
    """Tests the scripture reference finding logic."""

    def test_simple_reference(self):
        self.assertEqual(find_scripture_references("Show me John 3:16"), [('John', '3:16')])

    def test_reference_with_range(self):
        self.assertEqual(find_scripture_references("1 Corinthians 13:4-7 is a good one"), [('1 Corinthians', '13:4-7')])

    def test_abbreviated_book(self):
        self.assertEqual(find_scripture_references("I like Psa 23:1"), [('Psa', '23:1')])

    def test_multiple_references(self):
        self.assertEqual(find_scripture_references("John 3:16 and Gen 1:1"), [('John', '3:16'), ('Gen', '1:1')])

    def test_case_insensitivity(self):
        # The regex is case-insensitive, so the output should match the case in the input string.
        self.assertEqual(find_scripture_references("show me ROMANS 8:28"), [('ROMANS', '8:28')])


class TestDataManager(unittest.IsolatedAsyncioTestCase):
    """Tests the data_manager which connects to the SQLite database."""

    def setUp(self):
        """Clear caches before each test."""
        scripture_cache.clear()
        ongoing_fetches.clear()

    async def test_fetch_single_verse(self):
        """Test that a single verse can be fetched correctly."""
        text = await get_scripture_text("Genesis", "1:1")
        self.assertIn("In the beginning God created the heaven and the earth.", text)

    async def test_fetch_verse_range(self):
        """Test that a range of verses can be fetched."""
        text = await get_scripture_text("Genesis", "1:1-2")
        self.assertIn("In the beginning God created the heaven and the earth.", text)
        self.assertIn("And the earth was without form, and void", text)

    async def test_caching_works(self):
        """Test that results are cached to prevent redundant DB queries."""
        # First call should be a cache miss and populate the cache
        await get_scripture_text("John", "3:16")
        self.assertIn("kjv:john:3:16", scripture_cache)

        # Second call should be a cache hit
        # We can verify this by checking the print output (not ideal in tests) or by timing it
        import time
        start_time = time.time()
        await get_scripture_text("John", "3:16")
        duration = time.time() - start_time
        self.assertLess(duration, 0.01, "Second call should be much faster due to caching")

    async def test_error_handling_for_invalid_verse(self):
        """Test that a known error is raised for a verse that doesn't exist."""
        with self.assertRaises(VerseNotFoundError):
            await get_scripture_text("John", "99:99")

    async def test_error_caching(self):
        """Test that errors are also cached."""
        # First call should result in an error and cache it
        with self.assertRaises(VerseNotFoundError):
            await get_scripture_text("Genesis", "99:99")

        self.assertIn("kjv:genesis:99:99", scripture_cache)
        self.assertIsInstance(scripture_cache["kjv:genesis:99:99"], VerseNotFoundError)

    async def test_race_condition_handling(self):
        """Test that concurrent requests for the same verse result in only one DB query."""
        # We can't easily inspect the `ongoing_fetches` from here in a stable way,
        # but we can create concurrent tasks and check that they all get the same result
        # without erroring out.
        tasks = [get_scripture_text("Psalms", "23:1") for _ in range(3)]
        results = await asyncio.gather(*tasks)

        # All results should be identical
        self.assertEqual(len(results), 3)
        self.assertEqual(results[0], results[1])
        self.assertEqual(results[1], results[2])
        self.assertIn("The LORD is my shepherd", results[0])

if __name__ == '__main__':
    unittest.main()