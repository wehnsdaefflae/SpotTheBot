# coding=utf-8
import json
import random

from loguru import logger
from redis import Redis

from src.dataobjects import Snippet, User


class SnippetManager:
    def __init__(self, redis_conf: dict[str, str]):
        self.redis = Redis(**redis_conf)
        logger.info("Snippets initialized.")

        if self.redis.exists("snippet_id_counter"):
            self.snippet_count = int(self.redis.get("snippet_id_counter"))
        else:
            self.snippet_count = 0
            self.redis.set("snippet_id_counter", self.snippet_count)

    def set_snippet(self, text: str, source: str, is_bot: bool, metadata: dict[str, str]) -> str:
        # Store the snippet and its hash
        snippet_key = f"snippet:{self.snippet_count}"
        self.redis.hset(snippet_key, mapping={
            "text": text,
            "source": source,
            "is_bot": str(int(is_bot)),
            "metadata": json.dumps(metadata)
        })

        self.snippet_count = int(self.redis.incr("snippet_id_counter"))
        return snippet_key

    def get_snippet(self, snippet_id: int) -> Snippet:
        snippet_key = f"snippet:{snippet_id}"
        if not self.redis.exists(snippet_key):
            raise KeyError(f"Snippet {snippet_id} does not exist.")

        result = self.redis.hgetall(snippet_key)
        data = {
            key.decode(): value.decode()
            for key, value in result.items()
        }

        metadata = json.loads(data.pop("metadata"))
        return Snippet(data.pop("text"), data.pop("source"), bool(int(data.pop("is_bot"))), metadata, db_id=snippet_id)

    def get_next_snippet(self, user: User) -> Snippet:
        recent_snippet_ids = user.recent_snippet_ids
        while (random_snippet_id := random.randint(0, self.snippet_count - 1)) in recent_snippet_ids:
            pass
        recent_snippet_ids.append(random_snippet_id)
        snippet = self.get_snippet(random_snippet_id)
        return snippet

    def remove_snippet(self, snippet_id: int) -> None:
        snippet_key = f"snippet:{snippet_id}"
        if not self.redis.exists(snippet_key):
            raise KeyError(f"Snippet {snippet_id} does not exist.")
        self.redis.delete(snippet_key)
