from dataclasses import dataclass
from enum import Enum
from hashlib import sha256

import redislite


class Field(Enum):
    FALSE_POSITIVES = "false_positives"
    FALSE_NEGATIVES = "false_negatives"
    TRUE_POSITIVES = "true_positives"
    TRUE_NEGATIVES = "true_negatives"


# ----- User Database Functions -----

def update_user_performance(r: redislite.Redis, pseudonym: str, field: Field, value: int) -> None:
    # update_user_performance('JohnDoe', Field.FALSE_POSITIVES, 5)
    user_key = f"user:{pseudonym}"
    r.hset(user_key, field.value, str(value))


def get_user_performance_value(r: redislite.Redis, pseudonym: str, field: Field) -> int | None:
    # value = get_user_performance_value('JohnDoe', Field.FALSE_POSITIVES)
    # print(value)  # Outputs: 5
    user_key = f"user:{pseudonym}"
    value = r.hget(user_key, field.value)
    return int(value) if value else None


def set_user_progress(r: redislite.Redis, pseudonym: str, current_seed: int, from_snippet_id: int, to_snippet_id: int, current_index: int) -> None:
    user_key = f"user:{pseudonym}:progress"
    r.hset(user_key, mapping={
        "current_seed": current_seed,
        "from_snippet_id": from_snippet_id,
        "to_snippet_id": to_snippet_id,
        "current_index": current_index
    })


# ----- Snippet Database Functions -----

@dataclass(frozen=True)
class Snippet:
    snippet_id: int
    text: str
    source: str
    is_bot: bool
    metadata: dict[str, str]
    # date generated, model used, etc.


def set_snippet(r: redislite.Redis, text: str, source: str, is_bot: bool, metadata: dict[str, str]) -> int:
    # Check for duplicate snippet
    text_hash = sha256(text.encode()).hexdigest()
    if r.sismember("snippet_hashes", text_hash):
        raise ValueError("Duplicate snippet detected!")

    # Generate the next ID for the snippet
    snippet_id = r.incr("snippet_id_counter")

    # Store the snippet and its hash
    snippet_key = f"snippet:{snippet_id}"
    r.hset(snippet_key, mapping={
        "text": text,
        "source": source,
        "is_bot": int(is_bot),
        **metadata
    })
    r.sadd("snippet_hashes", text_hash)

    return snippet_id


def get_snippet(r: redislite.Redis, snippet_id: int) -> Snippet:
    snippet_key = f"snippet:{snippet_id}"
    result = r.hgetall(snippet_key)
    data = {
        key.decode(): (value.decode() if key.decode() != "is_bot" else bool(int(value.decode())))
        for key, value in result.items()
    }
    return Snippet(snippet_id, data.pop("text"), data.pop("source"), data.pop("is_bot"), data)


# ----- Marker Database Functions -----

def update_marker(r: redislite.Redis, marker_name: str, field: Field, value: int) -> None:
    # update_marker('repetitive', Field.TRUE_POSITIVE_COUNT, 10)
    marker_key = f"marker:{marker_name}"
    r.hset(marker_key, field.value, str(value))


def get_marker_value(r: redislite.Redis, marker_name: str, field: Field) -> int:
    # value = get_marker_value('repetitive', Field.TRUE_POSITIVE_COUNT)
    # print(value)  # Outputs: 10
    marker_key = f"marker:{marker_name}"
    value = r.hget(marker_key, field.value)
    return int(value) if value else None


def main() -> None:
    sources = {
        "recipes": "/home/mark/bananapi/home/mark/320GBNAS/kaggle/archive (0)/"

    }
    redis = redislite.Redis("spotthebot.rdb", db=0)
    set_snippet(redis, "Hello, world!", "https://example.com", False, dict())


if __name__ == '__main__':
    main()
