# coding=utf-8
import json
import subprocess
import sys

from loguru import logger
# import redislite.patch
# redislite.patch.patch_redis()

from redis import Redis

from loguru import logger
from redis.client import Pipeline

from src.dataobjects import StateUpdate, State, Friend, User, Face

logger.add(sys.stderr, format="{time} {level} {message}", colorize=True, level="INFO")
logger.add("logs/file_{time}.log", backtrace=True, diagnose=True, rotation="500 MB", level="DEBUG")


class Users:
    def __init__(self, redis_conf: dict[str, str], expiration_seconds: int = 60 * 60 * 24 * 7 * 30 * 6) -> None:
        self.redis = Redis(**redis_conf)
        logger.info("Users initialized.")

        self.expiration_seconds = expiration_seconds

        if not self.redis.exists("user_id_counter"):
            self.redis.set("user_id_counter", 0)

    def _reset_user_expiration(self, user_key: str, name_hash_key: str | None = None) -> None:
        if name_hash_key is None:
            secret_name_hash = self.redis.hget(user_key, "secret_name_hash")
            name_hash_key = f"name_hash:{secret_name_hash}"

        self.redis.expire(user_key, self.expiration_seconds)
        self.redis.expire(name_hash_key, self.expiration_seconds)
        friends_key = f"{user_key}:friends"
        self.redis.expire(friends_key, self.expiration_seconds)

    def create_user(self, user: User) -> str:
        name_hash_key = f"name_hash:{user.secret_name_hash}"
        if self.redis.exists(name_hash_key):
            raise ValueError("User already exists.")

        user_id = self.redis.incr("user_id_counter")
        user_key = f"user:{user_id}"
        self.redis.hset(user_key, mapping={
            "secret_name_hash": user.secret_name_hash,
            "face": json.dumps(user.face.to_tuple()),
            "last_positives_rate": user.state.last_positives_rate,
            "last_negatives_rate": user.state.last_negatives_rate,
            "invited_by_user_id": user.invited_by_user_id,
            "created_at": user.created_at,
        })
        self.redis.set(name_hash_key, user_id)

        # only friend of new user is invitee
        if user.invited_by_user_id >= 0:
            self.make_friends(user.invited_by_user_id, user_id)  # also initializes expiration

        logger.info(f"Created user {user_id}.")
        return user_key

    def get_user(self, secret_name_hash: str) -> User:
        # user = get_user('JohnDoe')
        # print(user)
        # Outputs:
        # User(secret_name_hash='JohnDoe', invited_by_user_id=243, created_at=1626374367.0, last_positives_rate=0.5,
        # last_negatives_rate=0.5, friends={482, 268})

        name_hash_key = f"name_hash:{secret_name_hash}"
        if not self.redis.exists(name_hash_key):
            raise KeyError(f"User with name hash {secret_name_hash} does not exist.")

        user_id = int(self.redis.get(name_hash_key))
        user_key = f"user:{user_id}"
        if not self.redis.exists(user_key):
            raise KeyError(f"User {user_id} does not exist.")

        result = self.redis.hgetall(user_key)
        data = {
            key.decode(): value.decode()
            for key, value in result.items()
        }

        friends = self.get_friends(user_id)
        state = State(data.pop("last_positives_rate"), data.pop("last_negatives_rate"))
        face_tuple = json.loads(data.pop("face"))
        face = Face(*face_tuple)
        return User(
            secret_name_hash=data.pop("secret_name_hash"),
            face=face,
            friends=friends,
            state=state,
            db_id=user_id,
            invited_by_user_id=data.pop("invited_by_user_id"),
            created_at=data.pop("created_at"),
        )

    def get_friend(self, friend_id: int) -> Friend:
        # friend = get_friend(345980)
        # print(friend)  # Outputs: Friend(db_id=345980, name='JohnDoe')
        user_key = f"user:{friend_id}"
        if not self.redis.exists(user_key):
            raise KeyError(f"User {friend_id} does not exist.")

        public_name = self.redis.hget(user_key, "public_name")
        return Friend(friend_id, str(public_name))

    def delete_user(self, user_id: int) -> None:
        # delete_user(243)
        user_key = f"user:{user_id}"
        if not self.redis.exists(user_key):
            raise KeyError(f"User {user_id} does not exist.")

        friends = self.get_friends(user_id)
        with self.redis.pipeline() as pipe:
            for each_friend in friends:
                self._remove_friend_unidirectional(each_friend.db_id, user_id, pipeline=pipe)
            pipe.execute()

        secret_name_hash = self.redis.hget(user_key, "secret_name_hash")

        self.redis.srem("user_name_hashes", secret_name_hash)
        self.redis.delete(f"{user_key}:progress")
        self.redis.delete(user_key)

    def make_friends(self, user_id: int, friend_id: int) -> None:
        # make_friends('JohnDoe', 'JaneDoe')
        user_key = f"user:{user_id}"
        if not self.redis.exists(user_key):
            raise KeyError(f"User {user_id} does not exist.")

        friend_key = f"user:{friend_id}"
        if not self.redis.exists(friend_key):
            raise KeyError(f"User {friend_id} does not exist.")

        users_friends_key = f"{user_key}:friends"
        friends_friends_key = f"{friend_key}:friends"

        self.redis.sadd(users_friends_key, friend_id)
        self.redis.sadd(friends_friends_key, user_id)

        self._reset_user_expiration(user_key)

    def _remove_friend_unidirectional(self, user_id: int, friend_id: int, pipeline: Pipeline | None) -> None:
        # remove_friend_unidirectional(234, 523)
        users_friends_key = f"user:{user_id}:friends"

        if pipeline is None:
            self.redis.srem(users_friends_key, friend_id)
        else:
            pipeline.srem(users_friends_key, friend_id)

    def remove_friendship(self, user_id: int, friend_id: int) -> None:
        # remove_friendship(234, 523)
        self._remove_friend_unidirectional(user_id, friend_id, pipeline=None)
        self._remove_friend_unidirectional(friend_id, user_id, pipeline=None)

        self._reset_user_expiration(f"user:{user_id}")

    def update_user_state(self, user_key: str, state_update: StateUpdate, minimum: int = 10) -> None:
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

        self.redis.hset(user_key, mapping={
            "last_positives_rate": positives_rate,
            "last_negatives_rate": negatives_rate
        })

        self._reset_user_expiration(user_key)

    def get_friends(self, user_id: int) -> set[Friend]:
        # friends = get_friends(345980)
        # print(friends)  # Outputs: {482, 268}
        user_key = f"user:{user_id}"
        users_friends_key = f"{user_key}:friends"

        friends = set()
        for friend_id_byte in self.redis.smembers(users_friends_key):
            each_friend = self.get_friend(int(friend_id_byte))
            friends.add(each_friend)

        return friends

    def set_user_progress(self, user_key: str, current_seed: int, from_snippet_id: int, to_snippet_id: int, current_index: int) -> None:
        progress_key = f"{user_key}:progress"
        self.redis.hset(progress_key, mapping={
            "current_seed": current_seed,
            "from_snippet_id": from_snippet_id,
            "to_snippet_id": to_snippet_id,
            "current_index": current_index
        })

        self._reset_user_expiration(user_key)
