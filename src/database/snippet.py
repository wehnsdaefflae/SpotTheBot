# coding=utf-8
import json
import subprocess

import loguru
import redislite.patch
redislite.patch.patch_redis()

from redis import Redis

from src.dataobjects import Snippet


class Snippets:
    def __init__(self, redis: Redis | None = None, debugging: bool = False):
        db_index = 1
        self.redis = redis or Redis("../database/spotthebot.rdb", db=1)
        loguru.logger.info(
            f"Snippets initialized. "
            f"`qredis -s {self.redis.connection_pool.connection_kwargs['path']} -n {db_index}`"
        )
        if debugging:
            subprocess.Popen(["qredis", "-s", self.redis.connection_pool.connection_kwargs['path'], "-n", str(db_index)])

        if self.redis.exists("snippet_id_counter"):
            self.snippet_count = self.redis.get("snippet_id_counter")
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

        self.snippet_count = self.redis.incr("snippet_id_counter")
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

    def remove_snippet(self, snippet_id: int) -> None:
        snippet_key = f"snippet:{snippet_id}"
        if not self.redis.exists(snippet_key):
            raise KeyError(f"Snippet {snippet_id} does not exist.")
        self.redis.delete(snippet_key)
