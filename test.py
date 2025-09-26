import unittest
import time
from scripture_finder import find_scripture_references
from api_client import get_scripture_text, VerseNotFoundError, scripture_cache

class TestScriptureFinder(unittest.TestCase):

    def test_simple_reference(self):
        self.assertEqual(find_scripture_references("Show me John 3:16"), [('John', '3:16')])

    def test_reference_with_range(self):
        self.assertEqual(find_scripture_references("1 Corinthians 13:4-7 is a good one"), [('1 Corinthians', '13:4-7')])

    def test_abbreviated_book(self):
        self.assertEqual(find_scripture_references("I like Psa 23:1"), [('Psa', '23:1')])

    def test_numbered_book_with_ordinal(self):
        self.assertEqual(find_scripture_references("Let's look at 1st samuel 1:1"), [('1st samuel', '1:1')])

    def test_no_scripture(self):
        self.assertEqual(find_scripture_references("This is just a regular sentence."), [])

    def test_multiple_references(self):
        # The implementation should find all references in the string.
        self.assertEqual(find_scripture_references("John 3:16 and Gen 1:1"), [('John', '3:16'), ('Gen', '1:1')])

    def test_book_with_space(self):
        self.assertEqual(find_scripture_references("Song of Solomon 1:1"), [('Song of Solomon', '1:1')])

    def test_case_insensitivity(self):
        self.assertEqual(find_scripture_references("show me ROMANS 8:28"), [('ROMANS', '8:28')])

class TestApiClient(unittest.TestCase):

    def setUp(self):
        """Clear the cache before each test."""
        scripture_cache.clear()

    def test_caching_works(self):
        # First call should be a miss
        get_scripture_text("Romans", "8:28")
        self.assertIn("romans:8:28", scripture_cache)

        # Time the second call to ensure it's faster (from cache)
        start_time = time.time()
        get_scripture_text("Romans", "8:28")
        end_time = time.time()
        self.assertLess(end_time - start_time, 0.1) # Should be almost instant

    def test_error_handling(self):
        with self.assertRaises(VerseNotFoundError):
            get_scripture_text("InvalidBook", "99:99")

    def test_error_caching(self):
        # First call should raise an error and cache it
        with self.assertRaises(VerseNotFoundError):
            get_scripture_text("Genesis", "1:99")

        self.assertIn("genesis:1:99", scripture_cache)
        self.assertIsInstance(scripture_cache["genesis:1:99"], VerseNotFoundError)

        # Second call should also raise the error, but from the cache
        start_time = time.time()
        with self.assertRaises(VerseNotFoundError):
            get_scripture_text("Genesis", "1:99")
        end_time = time.time()
        self.assertLess(end_time - start_time, 0.1)


if __name__ == '__main__':
    unittest.main()