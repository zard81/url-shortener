"""Tests for URL Shortener."""
import unittest
import tempfile
import os
from src.shortener import URLStore, validate_url


class TestURLStore(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.NamedTemporaryFile(suffix=".json", delete=False)
        self.tmp.close()
        self.store = URLStore(self.tmp.name)

    def tearDown(self):
        os.unlink(self.tmp.name)

    def test_add_url(self):
        url = self.store.add("https://example.com")
        self.assertEqual(url.original_url, "https://example.com")
        self.assertEqual(url.clicks, 0)

    def test_custom_code(self):
        url = self.store.add("https://example.com", custom_code="test")
        self.assertEqual(url.code, "test")
        self.assertTrue(url.custom)

    def test_duplicate_code(self):
        self.store.add("https://a.com", custom_code="dup")
        with self.assertRaises(ValueError):
            self.store.add("https://b.com", custom_code="dup")

    def test_click_tracking(self):
        url = self.store.add("https://example.com")
        self.store.click(url.code)
        self.store.click(url.code)
        self.assertEqual(self.store.get(url.code).clicks, 2)

    def test_delete(self):
        url = self.store.add("https://example.com")
        self.assertTrue(self.store.delete(url.code))
        self.assertIsNone(self.store.get(url.code))

    def test_stats(self):
        self.store.add("https://a.com")
        self.store.add("https://b.com")
        stats = self.store.stats()
        self.assertEqual(stats["total_urls"], 2)


class TestValidation(unittest.TestCase):
    def test_valid_urls(self):
        self.assertTrue(validate_url("https://example.com"))
        self.assertTrue(validate_url("http://localhost:8080/path"))

    def test_invalid_urls(self):
        self.assertFalse(validate_url("not-a-url"))
        self.assertFalse(validate_url(""))


if __name__ == "__main__":
    unittest.main()
