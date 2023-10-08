import dataclasses

import redislite


@dataclasses.dataclass(frozen=True)
class Snippet:
    snippet_id: int
    text: str
    source: str
    is_bot: bool
    metadata: dict[str, str]
    # date generated, model used, etc.


def set_snippet(r: redislite.Redis, text: str, source: str, is_bot: bool, metadata: dict[str, str]) -> str:
    snippet_id = r.incr("snippet_id_counter")

    # Store the snippet and its hash
    snippet_key = f"snippet:{snippet_id}"
    r.hset(snippet_key, mapping={
        "text": text,
        "source": source,
        "is_bot": int(is_bot),
        **metadata
    })

    return snippet_key


def get_snippet(r: redislite.Redis, snippet_id: int) -> Snippet:
    snippet_key = f"snippet:{snippet_id}"
    if not r.exists(snippet_key):
        raise KeyError(f"Snippet {snippet_id} does not exist.")

    result = r.hgetall(snippet_key)
    data = {
        key.decode(): (value.decode() if key.decode() != "is_bot" else bool(int(value.decode())))
        for key, value in result.items()
    }
    return Snippet(snippet_id, data.pop("text"), data.pop("source"), data.pop("is_bot"), data)


def remove_snippet(r: redislite.Redis, snippet_id: int) -> None:
    snippet_key = f"snippet:{snippet_id}"
    r.delete(snippet_key)
