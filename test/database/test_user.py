import hashlib
import os
import unittest
import redislite
from typing import Tuple

from loguru import logger

from src.database.user import StateUpdate, Users


class TestUsers(unittest.TestCase):

    def setUp(self) -> None:
        print("deleting last test database...")
        if os.path.isfile("test_spotthebot.rdb"):
            os.remove("test_spotthebot.rdb")
        if os.path.isfile("test_spotthebot.rdb.settings"):
            os.remove("test_spotthebot.rdb.settings")

        logger.info("Setting up user database tests.")
        self.redis = redislite.Redis("test_spotthebot.rdb", db=0)
        self.users = Users(redis=self.redis)

    def tearDown(self) -> None:
        self.redis.flushdb()
        self.redis.close()

    def create_two_users(self) -> Tuple[int, int]:
        secret_name_user = self.users.create_user("Jane Doe")
        secret_name_friend = self.users.create_user("John Doe")

        name_hash_user = hashlib.sha256(secret_name_user.encode()).hexdigest()
        name_hash_friend = hashlib.sha256(secret_name_friend.encode()).hexdigest()

        user = self.users.get_user(name_hash_user)
        friend = self.users.get_user(name_hash_friend)

        user_id = user.db_id
        friend_id = friend.db_id

        return user_id, friend_id

    def test_create_user(self) -> None:
        secret_name = self.users.create_user("John Doe")
        name_hash = hashlib.sha256(secret_name.encode()).hexdigest()
        user = self.users.get_user(name_hash)
        self.assertEqual(user.secret_name_hash, name_hash)

    def test_delete_user(self) -> None:
        secret_name = self.users.create_user("John Doe")
        name_hash = hashlib.sha256(secret_name.encode()).hexdigest()
        user = self.users.get_user(name_hash)
        user_id = user.db_id
        self.users.delete_user(user_id)

        user_key = f"user:{user_id}"
        self.assertFalse(self.redis.exists(user_key))

    def test_make_friends(self) -> None:
        user_id, friend_id = self.create_two_users()

        self.users.make_friends(user_id, friend_id)

        self.assertTrue(friend_id in {each_friend.db_id for each_friend in self.users.get_friends(user_id)})
        self.assertTrue(user_id in {each_friend.db_id for each_friend in self.users.get_friends(friend_id)})

    def test_remove_friendship(self) -> None:
        user_id, friend_id = self.create_two_users()

        self.users.make_friends(user_id, friend_id)
        self.users.remove_friendship(user_id, friend_id)

        self.assertFalse(friend_id in {each_friend.db_id for each_friend in self.users.get_friends(user_id)})
        self.assertFalse(user_id in {each_friend.db_id for each_friend in self.users.get_friends(friend_id)})

    def test_update_user_state(self) -> None:
        secret_name = self.users.create_user("John Doe")
        name_hash = hashlib.sha256(secret_name.encode()).hexdigest()
        user = self.users.get_user(name_hash)
        user_id = user.db_id

        state_update = StateUpdate(10, 10, 5, 5)
        user_key = f"user:{user_id}"
        self.users.update_user_state(user_key, state_update)

        last_positives_rate = float(self.redis.hget(user_key, "last_positives_rate"))
        last_negatives_rate = float(self.redis.hget(user_key, "last_negatives_rate"))

        self.assertEqual(last_positives_rate, 0.6666666666666666)
        self.assertEqual(last_negatives_rate, 0.6666666666666666)

    def test_get_friends(self) -> None:
        user_id, friend_id = self.create_two_users()

        self.users.make_friends(user_id, friend_id)
        friends = self.users.get_friends(user_id)
        self.assertTrue(friend_id in {each_friend.db_id for each_friend in friends})

    def test_set_user_progress(self) -> None:
        secret_name = self.users.create_user("John Doe")
        name_hash = hashlib.sha256(secret_name.encode()).hexdigest()
        user = self.users.get_user(name_hash)
        user_id = user.db_id

        self.users.set_user_progress(f"user:{user_id}", 1, 100, 200, 150)

        user_key: str = f"user:{user_id}"
        progress_key: str = f"{user_key}:progress"
        current_seed: int = int(self.redis.hget(progress_key, "current_seed"))
        from_snippet_id: int = int(self.redis.hget(progress_key, "from_snippet_id"))
        to_snippet_id: int = int(self.redis.hget(progress_key, "to_snippet_id"))
        current_index: int = int(self.redis.hget(progress_key, "current_index"))

        self.assertEqual(current_seed, 1)
        self.assertEqual(from_snippet_id, 100)
        self.assertEqual(to_snippet_id, 200)
        self.assertEqual(current_index, 150)


if __name__ == "__main__":
    unittest.main()
