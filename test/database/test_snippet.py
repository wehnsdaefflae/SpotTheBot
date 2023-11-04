import json
import unittest
from loguru import logger

from src.database.snippet_manager import SnippetManager


class TestSnippets(unittest.TestCase):

    def setUp(self):
        logger.info(f"Starting up snippet database tests.")

        with open("../../config.json", mode="r") as config_file:
            config = json.load(config_file)

        self.max_markers = 10
        database_config = config.pop("redis")
        snippets_config = database_config.pop("snippets_database")
        snippets_config["db"] += 10  # test index
        self.db_index = snippets_config["db"]

        self.snippets = SnippetManager(snippets_config)

    def tearDown(self):
        self.snippets.redis.select(self.db_index)
        self.snippets.redis.flushdb()

    def test_set_snippet(self):
        key = self.snippets.set_snippet("Sample text", "Sample source", True, {"tag": "test"})
        self.assertTrue(self.snippets.redis.exists(key))

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
        self.assertFalse(self.snippets.redis.exists(key))

    def test_remove_snippet_nonexistent(self):
        with self.assertRaises(KeyError):
            self.snippets.remove_snippet(9999)  # Assuming 9999 doesn't exist

    def test_get_snippet_nonexistent(self):
        with self.assertRaises(KeyError):
            self.snippets.get_snippet(9999)  # Assuming 9999 doesn't exist


if __name__ == '__main__':
    unittest.main()
