import unittest
from scripture_finder import find_scripture_references

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
        # The current implementation only finds the first one. This test will reflect that.
        self.assertEqual(find_scripture_references("John 3:16 and Gen 1:1"), [('John', '3:16'), ('Gen', '1:1')])

    def test_book_with_space(self):
        self.assertEqual(find_scripture_references("Song of Solomon 1:1"), [('Song of Solomon', '1:1')])

    def test_case_insensitivity(self):
        self.assertEqual(find_scripture_references("show me ROMANS 8:28"), [('ROMANS', '8:28')])

if __name__ == '__main__':
    unittest.main()