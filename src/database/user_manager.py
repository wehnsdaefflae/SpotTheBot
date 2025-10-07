# coding=utf-8
import hashlib
import json
from collections import deque

from redis import Redis

from loguru import logger
from redis.client import Pipeline

from src.dataobjects import Friend, User, Face


class UserManager:
    def __init__(self, redis_conf: dict[str, str], expiration_seconds: int = 60 * 60 * 24 * 7 * 4 * 6) -> None:
        self.redis = Redis(**redis_conf)
        logger.info("Users initialized.")

        self.expiration_seconds = expiration_seconds

    def _reset_user_expiration(self, user_key: str, name_hash_key: str | None = None) -> None:
        if name_hash_key is None:
            secret_name_hash = self.redis.hget(user_key, "secret_name_hash")
            name_hash_key = f"name_hash:{secret_name_hash}"

        self.redis.expire(user_key, self.expiration_seconds)
        self.redis.expire(name_hash_key, self.expiration_seconds)

    def create_user(self, secret_name: str, face: Face, public_name: str, invited_by_user_id: int) -> User:
        secret_name_hash = hashlib.sha256(secret_name.encode()).hexdigest()
        name_hash_key = f"name_hash:{secret_name_hash}"
        if self.redis.exists(name_hash_key):
            raise ValueError("User already exists.")

        user_id = int(self.redis.incr("user_id_counter"))
        user_key = f"user:{user_id}"
        user = User(
            secret_name_hash=secret_name_hash,
            public_name=public_name,
            face=face,
            db_id=user_id,
            invited_by_user_id=invited_by_user_id
        )
        self.redis.hset(user_key, mapping={
            "secret_name_hash":     secret_name_hash,
            "public_name":          public_name,
            "penalty":              int(user.penalty),
            "face":                 face.source_id,
            "true_positives":       float(user.true_positives),
            "true_negatives":       float(user.true_negatives),
            "false_positives":      float(user.false_positives),
            "false_negatives":      float(user.false_negatives),
            "db_id":                user_id,
            "invited_by_user_id":   invited_by_user_id,
            "created_at":           user.created_at,
            "recent_snippet_ids":   json.dumps(list(user.recent_snippet_ids)),
        })
        self.redis.set(name_hash_key, user_id)

        # only friend of new user is invitee
        if invited_by_user_id >= 0:
            self.make_friends(invited_by_user_id, user_id)  # also initializes expiration

        logger.info(f"Created user {user_id}.")
        return user

    def get_user_by_id(self, user_id: int) -> User | None:
        user_key = f"user:{user_id}"
        if not self.redis.exists(user_key):
            return None

        result = self.redis.hgetall(user_key)
        data = {
            key.decode(): value.decode()
            for key, value in result.items()
        }

        true_positives = float(data.pop("true_positives"))
        true_negatives = float(data.pop("true_negatives"))
        false_positives = float(data.pop("false_positives"))
        false_negatives = float(data.pop("false_negatives"))

        face = Face(data.pop("face"))
        recent_snippet_ids = json.loads(data.pop("recent_snippet_ids"))
        user = User(
            secret_name_hash=data.pop("secret_name_hash"),
            public_name=data.pop("public_name"),
            penalty=bool(int(data.pop("penalty"))),
            face=face,
            true_positives=true_positives,
            true_negatives=true_negatives,
            false_positives=false_positives,
            false_negatives=false_negatives,
            db_id=user_id,
            invited_by_user_id=data.pop("invited_by_user_id"),
            created_at=data.pop("created_at"),
            recent_snippet_ids=deque(recent_snippet_ids)
        )
        return user

    def get_user(self, secret_name_hash: str) -> User | None:
        name_hash_key = f"name_hash:{secret_name_hash}"
        if not self.redis.exists(name_hash_key):
            return None

        user_id = int(self.redis.get(name_hash_key))
        return self.get_user_by_id(user_id)

    def delete_user(self, user_id: int) -> None:
        # delete_user(243)
        user_key = f"user:{user_id}"
        if not self.redis.exists(user_key):
            raise KeyError(f"User {user_id} does not exist.")

        secret_name_hash = self.redis.hget(user_key, "secret_name_hash")
        name_hash_key = f"name_hash:{secret_name_hash.decode()}"
        if not self.redis.exists(name_hash_key):
            raise KeyError(f"User with name hash {secret_name_hash} does not exist.")

        friends = self.get_friends(user_id)

        with self.redis.pipeline() as pipe:
            for each_friend in friends:
                self._remove_friend_unidirectional(each_friend.db_id, user_id, pipeline=pipe)
            pipe.execute()

        self.redis.delete(name_hash_key)
        self.redis.delete(user_key)

    def make_friends(self, user_id: int, friend_id: int) -> None:
        # make_friends('JohnDoe', 'JaneDoe')
        if user_id == friend_id:
            raise ValueError("Cannot befriend oneself.")

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

    def get_friends(self, user_id: int) -> set[Friend]:
        users_friends_key = f"user:{user_id}:friends"
        friends = set()
        if not self.redis.exists(users_friends_key):
            return friends

        friend_ids = self.redis.smembers(users_friends_key)
        for each_friend_id in friend_ids:
            friend_key = f"user:{each_friend_id.decode()}"
            if not self.redis.exists(friend_key):
                raise KeyError(f"User {friend_key} does not exist.")

            face_id = self.redis.hget(friend_key, "face")
            public_name = self.redis.hget(friend_key, "public_name")
            false_positives = float(self.redis.hget(friend_key, "false_positives"))
            true_positives = float(self.redis.hget(friend_key, "true_positives"))
            false_negatives = float(self.redis.hget(friend_key, "false_negatives"))
            true_negatives = float(self.redis.hget(friend_key, "true_negatives"))
            positives = false_positives + true_positives
            negatives = false_negatives + true_negatives
            anger = 0. if 0 >= positives else false_positives / positives
            sadness = 0. if 0 >= negatives else false_negatives / negatives
            wins = int(true_positives + true_negatives)
            each_friend = Friend(
                db_id=int(each_friend_id),
                name=public_name.decode(),
                face=Face(face_id.decode()),
                anger=anger,
                sadness=sadness,
                wins=wins,
            )
            friends.add(each_friend)

        return friends

    def set_user_penalty(self, user: User, penalty: bool) -> None:
        user_key = f"user:{user.db_id}"
        self.redis.hset(user_key, mapping={
            "penalty": int(penalty)
        })

        self._reset_user_expiration(user_key)

    def update_user_state(self, user: User,
                          true_positive: float, false_positive: float,
                          true_negative: float, false_negative: float) -> None:

        user_key = f"user:{user.db_id}"

        self.redis.hset(user_key, mapping={
            "true_positives": true_positive,
            "false_positives": false_positive,
            "true_negatives": true_negative,
            "false_negatives": false_negative,
            "penalty": 0
        })

        self._reset_user_expiration(user_key)
