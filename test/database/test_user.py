import time
from collections import deque
import json
import unittest

from loguru import logger

from src.database.user_manager import UserManager
from src.dataobjects import Face, User, State


class TestUsers(unittest.TestCase):

    def setUp(self) -> None:
        logger.info(f"Starting up user database tests.")

        with open("../../config.json", mode="r") as config_file:
            config = json.load(config_file)

        self.max_markers = 10
        database_config = config.pop("redis")
        users_config = database_config.pop("users_database")
        users_config["db"] += 10  # test index
        self.db_index = users_config["db"]

        self.users = UserManager(users_config)
        self.redis = self.users.redis

    def tearDown(self) -> None:
        self.redis.flushdb()
        self.redis.close()

    def test_create_user(self):
        secret_name = "testuser"
        face = Face()
        public_name = "Test User"
        invited_by_user_id = 1

        user = self.users.create_user(secret_name, face, public_name, invited_by_user_id)

        self.assertIsNotNone(user)
        self.assertEqual(user.public_name, public_name)
        self.assertEqual(user.invited_by_user_id, invited_by_user_id)
        self.assertEqual(user.face, face)

    def test_get_user(self):
        user = self.users.create_user("testuser", Face(), "Test User", -1)
        secret_name_hash = user.secret_name_hash

        retrieved_user = self.users.get_user(secret_name_hash)

        self.assertIsNotNone(retrieved_user)
        self.assertEqual(retrieved_user.db_id, user.db_id)
        self.assertEqual(retrieved_user.public_name, "Test User")

    def test_delete_user(self):
        user = self.users.create_user("testuser", Face(), "Test User", -1)

        self.users.delete_user(user.db_id)

        self.assertFalse(self.redis.exists(f"user:{user.db_id}"))
        self.assertFalse(self.redis.exists(f"name_hash:{user.secret_name_hash}"))

    def test_make_friends(self):
        user_1 = self.users.create_user("testuser1", Face(), "Test User 1", -1)
        user_id_1 = user_1.db_id
        user_2 = self.users.create_user("testuser2", Face(), "Test User 2", -1)
        user_id_2 = user_2.db_id

        self.users.make_friends(user_id_1, user_id_2)

        friends_of_user_1 = self.redis.smembers(f"user:{user_id_1}:friends")
        friends_of_user_2 = self.redis.smembers(f"user:{user_id_2}:friends")

        self.assertIn(str(user_id_2).encode(), friends_of_user_1)
        self.assertIn(str(user_id_1).encode(), friends_of_user_2)

    def test_remove_friendship(self):
        user_1 = self.users.create_user("testuser1", Face(), "Test User 1", -1)
        user_id_1 = user_1.db_id
        user_2 = self.users.create_user("testuser2", Face(), "Test User 2", -1)
        user_id_2 = user_2.db_id

        self.users.make_friends(user_id_1, user_id_2)
        self.users.remove_friendship(user_id_1, user_id_2)

        friends_of_user_1 = self.redis.smembers(f"user:{user_id_1}:friends")
        friends_of_user_2 = self.redis.smembers(f"user:{user_id_2}:friends")

        self.assertNotIn(str(user_id_2).encode(), friends_of_user_1)
        self.assertNotIn(str(user_id_1).encode(), friends_of_user_2)

    def test_get_friends(self):
        user = self.users.create_user("testuser1", Face(), "Test User 1", -1)
        user_id = user.db_id
        friend = self.users.create_user("testuser2", Face(), "Test User 2", -1)
        friend_id = friend.db_id

        self.users.make_friends(user_id, friend_id)

        friends = self.users.get_friends(user_id)
        self.assertEqual(len(friends), 1)
        friend, = friends
        self.assertEqual(friend.db_id, friend_id)

        friends = self.users.get_friends(friend_id)
        self.assertEqual(len(friends), 1)
        friend, = friends
        self.assertEqual(friend.db_id, user_id)

    def test_set_user_penalty(self):
        user = self.users.create_user("testuser1", Face(), "Test User 1", -1)

        self.users.set_user_penalty(user, True)
        penalty = self.redis.hget(f"user:{user.db_id}", "penalty").decode('utf-8')
        self.assertEqual(int(penalty), 1)

        self.users.set_user_penalty(user, False)
        penalty = self.redis.hget(f"user:{user.db_id}", "penalty").decode('utf-8')
        self.assertEqual(int(penalty), 0)

    def test_update_user_state_positive_how_true_positive(self):
        user = self.users.create_user("testuser1", Face(), "Test User 1", -1)

        self.users.update_user_state(user, True, 5, 10)
        precision = float(self.redis.hget(f"user:{user.db_id}", "precision").decode('utf-8'))
        expected = (.5 * (10 - 5) + (1. * 5)) / 10
        self.assertAlmostEqual(precision, expected)

    def test_update_user_state_positive_how_true_negative(self):
        user = self.users.create_user("testuser1", Face(), "Test User 1", -1)

        self.users.update_user_state(user, True, -5, 10)
        precision = float(self.redis.hget(f"user:{user.db_id}", "precision").decode('utf-8'))
        expected = (.5 * (10 + -5)) / 10
        self.assertAlmostEqual(precision, expected)

    def test_update_user_state_negative_how_true_positive(self):
        user = self.users.create_user("testuser1", Face(), "Test User 1", -1)

        self.users.update_user_state(user, False, 5, 10)
        specificity = float(self.redis.hget(f"user:{user.db_id}", "specificity").decode('utf-8'))
        expected = (.5 * (10 - 5) + (1. * 5)) / 10
        self.assertAlmostEqual(specificity, expected)

    def test_update_user_state_negative_how_true_negative(self):
        user = self.users.create_user("testuser1", Face(), "Test User 1", -1)

        self.users.update_user_state(user, False, -5, 10)
        specificity = float(self.redis.hget(f"user:{user.db_id}", "specificity").decode('utf-8'))
        expected = (.5 * (10 + -5)) / 10
        self.assertAlmostEqual(specificity, expected)

    if __name__ == '__main__':
        unittest.main()


if __name__ == "__main__":
    unittest.main()
