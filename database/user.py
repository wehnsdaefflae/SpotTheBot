import dataclasses
import sys
import time

import redislite
from loguru import logger

logger.add(sys.stderr, format="{time} {level} {message}", colorize=True, level="INFO")
logger.add("file_{time}.log", backtrace=True, diagnose=True, rotation="500 MB", level="DEBUG")


EXPIRATION_SECONDS: int = 60 * 60 * 24 * 7 * 30 * 6


@dataclasses.dataclass(frozen=True)
class StateUpdate:
    true_positives: int
    true_negatives: int
    false_positives: int
    false_negatives: int


def _reset_user_expiration(r: redislite.Redis, user_key: str) -> None:
    secret_name_hash = r.hget(user_key, "secret_name_hash")
    r.expire(user_key, EXPIRATION_SECONDS)
    r.expire(f"name_hash:{secret_name_hash}", EXPIRATION_SECONDS)


def create_user(r: redislite.Redis, secret_name_hash: str, invited_by_user_id: int | None = None) -> str:
    if r.exists(f"name_hash:{secret_name_hash}"):
        raise ValueError(f"User with name hash {secret_name_hash} already exists.")

    user_id = r.incr("user_id_counter")
    user_key = f"user:{user_id}"
    r.hset(user_key, mapping={
        "secret_name_hash": secret_name_hash,
        "invited_by_user_id": invited_by_user_id or -1,
        "created_at": time.time(),
        "last_positives_rate": .5,
        "last_negatives_rate": .5
    })

    r.expire(user_key, EXPIRATION_SECONDS)

    name_hash_key = f"name_hash:{secret_name_hash}"
    r.set(name_hash_key, user_id)
    r.expire(name_hash_key, EXPIRATION_SECONDS)

    if invited_by_user_id is not None:
        make_friends(r, invited_by_user_id, user_id)

    return user_key


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

    secret_name_hash = r.hget(user_key, "secret_name_hash")

    r.srem("user_name_hashes", secret_name_hash)
    r.delete(f"{user_key}:progress")
    r.delete(user_key)


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

    _reset_user_expiration(r, user_key)


def remove_friend_unidirectional(r: redislite.Redis, user_id: int, friend_id: int, pipeline: "Pipeline" | None) -> None:
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

    _reset_user_expiration(r, user_key)


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

    _reset_user_expiration(r, user_key)

