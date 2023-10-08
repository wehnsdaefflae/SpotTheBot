import time
import dataclasses
import sys
from dataclasses import dataclass
from enum import Enum
from loguru import logger

import redislite
from redis.client import Pipeline

logger.add(sys.stderr, format="{time} {level} {message}", colorize=True, level="INFO")
logger.add("file_{time}.log", backtrace=True, diagnose=True, rotation="500 MB", level="DEBUG")


class Field(Enum):
    FALSE_POSITIVES = "false_positives"
    FALSE_NEGATIVES = "false_negatives"
    TRUE_POSITIVES = "true_positives"
    TRUE_NEGATIVES = "true_negatives"


@dataclasses.dataclass(frozen=True)
class StateUpdate:
    true_positives: int
    true_negatives: int
    false_positives: int
    false_negatives: int


# ----- Initialization Functions -----
def initialize_counters(r: redislite.Redis):
    if not r.exists("user_id_counter"):
        r.set("user_id_counter", 0)

    if not r.exists("snippet_id_counter"):
        r.set("snippet_id_counter", 0)


# ----- User Database Functions -----

def create_user(r: redislite.Redis, secret_name_hash: str, invited_by_user_id: int | None = None) -> str:
    if r.sismember("user_name_hashes", secret_name_hash):
        raise ValueError(f"User with name hash {secret_name_hash} already exists.")

    r.sadd("user_name_hashes", secret_name_hash)

    user_id = r.incr("user_id_counter")
    user_key = f"user:{user_id}"

    r.hset(user_key, mapping={
        "secret_name_hash": secret_name_hash,
        "invited_by_user_id": invited_by_user_id or -1,
        "created_at": time.time(),
        "last_positives_rate": .5,
        "last_negatives_rate": .5
    })

    if invited_by_user_id is not None:
        make_friends(r, invited_by_user_id, user_id)

    return user_key


def make_friends(r: redislite.Redis, user_id: int, friend_id: int) -> None:
    # make_friends('JohnDoe', 'JaneDoe')
    user_key = f"user:{user_id}"
    if not r.exists(user_key):
        raise KeyError(f"User {user_id} does not exist.")

    users_friends_key = f"{user_key}:friends"
    r.sadd(users_friends_key, friend_id)

    friend_key = f"user:{friend_id}"
    if not r.exists(friend_key):
        raise KeyError(f"User {friend_id} does not exist.")

    friends_friends_key = f"{friend_key}:friends"
    r.sadd(friends_friends_key, user_id)


def remove_friend_unidirectional(r: redislite.Redis, user_id: int, friend_id: int, pipeline: Pipeline | None) -> None:
    # remove_friend_unidirectional(234, 523)
    users_friends_key = f"user:{user_id}:friends"

    if pipeline is None:
        r.srem(users_friends_key, friend_id)
    else:
        pipeline.srem(f"user:{user_id}:friends", friend_id)


def remove_friendship(r: redislite.Redis, user_id: int, friend_id: int) -> None:
    # remove_friendship(234, 523)
    remove_friend_unidirectional(r, user_id, friend_id, pipeline=None)
    remove_friend_unidirectional(r, friend_id, user_id, pipeline=None)


def delete_user(r: redislite.Redis, user_id: int) -> None:
    # delete_user(243)
    user_key = f"user:{user_id}"
    if not r.exists(user_key):
        raise KeyError(f"User {user_id} does not exist.")

    friends = get_friends(r, user_id)
    with r.pipeline() as pipe:
        for each_friend_id in friends:
            remove_friend_unidirectional(r, each_friend_id, user_id, pipeline=pipe)
        pipe.execute()

    r.delete(user_key)
    r.delete(f"{user_key}:progress")


def update_user_state(r: redislite.Redis, user_key: str, state_update: StateUpdate, minimum: int = 10) -> None:
    # update_user_state('JohnDoe', StateUpdate(0, 0, 1, 0))
    if state_update.true_positives + state_update.false_positives + state_update.true_negatives + state_update.false_negatives < minimum:
        return

    positives = state_update.true_positives + state_update.false_positives
    if positives < 1:
        return
    positives_rate = state_update.true_positives / positives

    negatives = state_update.true_negatives + state_update.false_negatives
    if negatives < 1:
        return
    negatives_rate = state_update.true_negatives / negatives

    r.hset(user_key, mapping={
        "last_positives_rate": positives_rate,
        "last_negatives_rate": negatives_rate
    })


def get_friends(r: redislite.Redis, user_id: int) -> set[int]:
    # friends = get_friends(345980)
    # print(friends)  # Outputs: {482, 268}
    friends_key = f"user:{user_id}:friends"
    friends = r.smembers(friends_key)
    return set(int(friend_id) for friend_id in friends)


def set_user_progress(r: redislite.Redis, user_key: str, current_seed: int, from_snippet_id: int, to_snippet_id: int, current_index: int) -> None:
    progress_key = f"{user_key}:progress"
    r.hset(progress_key, mapping={
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


# ----- Marker Database Functions -----

def increment_marker(r: redislite.Redis, marker_name: str, field: Field) -> None:
    # increment_marker('repetitive', Field.TRUE_POSITIVE_COUNT)
    marker_key = f"marker:{marker_name}"
    marker_field_key = f"{marker_key}:{field.value}"
    r.incr(marker_field_key)

    marker_update_key = f"{marker_key}:last_update"
    r.set(marker_update_key, time.time())


def get_marker_value(r: redislite.Redis, marker_name: str, field: Field) -> int:
    # value = get_marker_value('repetitive', Field.TRUE_POSITIVE_COUNT)
    # print(value)  # Outputs: 10
    marker_field_key = f"marker:{marker_name}:{field.value}"
    value = r.get(marker_field_key)
    return int(value) if value else 0


def remove_marker(r: redislite.Redis, marker_name: str) -> None:
    # remove_marker('repetitive')
    marker_keys_pattern = f"marker:{marker_name}:*"
    keys_to_delete = r.keys(marker_keys_pattern)

    # Delete each key
    with r.pipeline() as pipe:
        for key in keys_to_delete:
            r.delete(key)
        pipe.execute()


def main() -> None:
    # todo:
    #  - set key expiration

    redis = redislite.Redis("spotthebot.rdb", db=0)

    initialize_counters(redis)

    sources = {
        "recipes": "/home/mark/bananapi/home/mark/320GBNAS/kaggle/archive (0)/"

    }
    set_snippet(redis, "Hello, world!", "https://example.com", False, dict())


if __name__ == '__main__':
    main()
