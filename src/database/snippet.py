import dataclasses
import json

import redislite


@dataclasses.dataclass(frozen=True)
class Snippet:
    snippet_id: int
    text: str
    source: str
    is_bot: bool
    metadata: tuple[tuple[str, str], ...]


class Snippets:
    def __init__(self, redis: redislite.Redis):
        self.redis = redis
        if not self.redis.exists("snippet_id_counter"):
            self.redis.set("snippet_id_counter", 0)

    def set_snippet(self, text: str, source: str, is_bot: bool, metadata: dict[str, str]) -> str:
        snippet_id = self.redis.incr("snippet_id_counter")

        # Store the snippet and its hash
        snippet_key = f"snippet:{snippet_id}"
        self.redis.hset(snippet_key, mapping={
            "text": text,
            "source": source,
            "is_bot": str(int(is_bot)),
            "metadata": json.dumps(metadata)
        })

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
        return Snippet(snippet_id, data.pop("text"), data.pop("source"), bool(int(data.pop("is_bot"))), metadata)

    def remove_snippet(self, snippet_id: int) -> None:
        snippet_key = f"snippet:{snippet_id}"
        if not self.redis.exists(snippet_key):
            raise KeyError(f"Snippet {snippet_id} does not exist.")
        self.redis.delete(snippet_key)
