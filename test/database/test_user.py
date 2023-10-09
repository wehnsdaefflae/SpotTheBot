import unittest
import redislite
from typing import Tuple

from loguru import logger

from src.database.user import StateUpdate, Users


class TestUsers(unittest.TestCase):

    def setUp(self) -> None:
        logger.info("Setting up user database tests.")
        self.redis = redislite.Redis("test_spotthebot.rdb", db=0)
        self.users = Users(redis=self.redis)

    def tearDown(self) -> None:
        self.redis.flushdb()
        self.redis.close()

    def create_two_users(self) -> Tuple[int, int]:
        user_name = "John Doe"
        friend_name = "Mary Jane"
        user_id = int(self.users.create_user(user_name).split(":")[1])
        friend_id = int(self.users.create_user(friend_name).split(":")[1])
        return user_id, friend_id

    def test_create_user(self) -> None:
        user_name: str = "Cristiano Ronaldo"
        user_key: str = self.users.create_user(user_name)
        self.assertTrue(self.redis.exists(user_key))

        with self.assertRaises(ValueError):
            self.users.create_user(user_name)  # trying to create user with the same name should raise ValueError

    def test_delete_user(self) -> None:
        user_name: str = "Fernando Torres"
        user_id = int(self.users.create_user(user_name).split(":")[1])
        self.users.delete_user(user_id)
        user_key: str = f"user:{user_id}"
        self.assertFalse(self.redis.exists(user_key))

    def test_make_friends(self) -> None:
        user_id, friend_id = self.create_two_users()

        self.users.make_friends(user_id, friend_id)

        self.assertTrue(friend_id in self.users.get_friends(user_id))
        self.assertTrue(user_id in self.users.get_friends(friend_id))

    def test_remove_friendship(self) -> None:
        user_id, friend_id = self.create_two_users()

        self.users.make_friends(user_id, friend_id)
        self.users.remove_friendship(user_id, friend_id)

        self.assertFalse(friend_id in self.users.get_friends(user_id))
        self.assertFalse(user_id in self.users.get_friends(friend_id))

    def test_update_user_state(self) -> None:
        user_name: str = "Eden Hazard"
        user_id = int(self.users.create_user(user_name).split(":")[1])
        state_update: StateUpdate = StateUpdate(10, 10, 5, 5)
        user_key: str = f"user:{user_id}"
        self.users.update_user_state(user_key, state_update)

        last_positives_rate: float = float(self.redis.hget(user_key, "last_positives_rate"))
        last_negatives_rate: float = float(self.redis.hget(user_key, "last_negatives_rate"))

        self.assertEqual(last_positives_rate, 0.6666666666666666)
        self.assertEqual(last_negatives_rate, 0.6666666666666666)

    def test_get_friends(self) -> None:
        user_id, friend_id = self.create_two_users()

        self.users.make_friends(user_id, friend_id)
        friends: set[int] = self.users.get_friends(user_id)
        self.assertTrue(friend_id in friends)

    def test_set_user_progress(self) -> None:
        user_name: str = "Andres Iniesta"
        user_id = int(self.users.create_user(user_name).split(":")[1])
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
