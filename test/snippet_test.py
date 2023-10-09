import unittest
import redislite

from src.database.snippet import Snippets


class TestSnippets(unittest.TestCase):

    def setUp(self):
        self.redis = redislite.Redis("../database/test_spotthebot.rdb", db=2)
        self.snippets = Snippets(self.redis)

    def tearDown(self):
        self.redis.flushall()
        self.redis.close()

    def test_set_snippet(self):
        key = self.snippets.set_snippet("Sample text", "Sample source", True, {"tag": "test"})
        self.assertTrue(self.redis.exists(key))

    def test_get_snippet(self):
        key = self.snippets.set_snippet("Sample text", "Sample source", True, {"tag": "test"})
        snippet_id = int(key.split(":")[1])
        snippet = self.snippets.get_snippet(snippet_id)

        self.assertEqual(snippet.text, "Sample text")
        self.assertEqual(snippet.source, "Sample source")
        self.assertEqual(snippet.is_bot, True)
        self.assertEqual(snippet.metadata, {"tag": "test"})

    def test_remove_snippet(self):
        key = self.snippets.set_snippet("Sample text", "Sample source", True, {"tag": "test"})
        snippet_id = int(key.split(":")[1])

        self.snippets.remove_snippet(snippet_id)
        self.assertFalse(self.redis.exists(key))

    def test_remove_snippet_nonexistent(self):
        with self.assertRaises(KeyError):
            self.snippets.remove_snippet(9999)  # Assuming 9999 doesn't exist

    def test_get_snippet_nonexistent(self):
        with self.assertRaises(KeyError):
            self.snippets.get_snippet(9999)  # Assuming 9999 doesn't exist


if __name__ == '__main__':
    unittest.main()
