import unittest

import redislite

from src.database.marker import Markers, Field


class TestMarkers(unittest.TestCase):

    def setUp(self) -> None:
        self.redis = redislite.Redis("../database/test_spotthebot.rdb", db=1)
        self.markers = Markers(self.redis)

    def tearDown(self) -> None:
        self.redis.flushall()
        self.redis.close()

    def test_increment_marker(self) -> None:
        self.markers.increment_marker("test_marker", Field.TRUE_POSITIVES)
        value = self.markers.get_marker_value("test_marker", Field.TRUE_POSITIVES)
        self.assertEqual(value, 1)

    def test_remove_marker(self) -> None:
        self.markers.increment_marker("test_marker", Field.TRUE_POSITIVES)
        self.markers.remove_marker("test_marker")
        value = self.markers.get_marker_value("test_marker", Field.TRUE_POSITIVES)
        self.assertEqual(value, 0)

    def test_max_markers(self) -> None:
        for i in range(150):  # Add 150 markers
            each_marker_name = f"marker_{i}"
            self.markers.increment_marker(each_marker_name, Field.TRUE_POSITIVES)

        # Make sure we only have 100 markers
        markers_list_length = self.redis.llen("markers_list")
        self.assertEqual(markers_list_length, 100)

        # Check if the oldest markers are removed
        self.assertIsNone(self.redis.hget("marker:marker_0", Field.TRUE_POSITIVES.value))
        self.assertIsNone(self.redis.hget("marker:marker_49", Field.TRUE_POSITIVES.value))
        self.assertIsNotNone(self.redis.hget("marker:marker_50", Field.TRUE_POSITIVES.value))

    def test_update_marker_list(self) -> None:
        self.markers.increment_marker("marker_1", Field.TRUE_POSITIVES)
        self.markers.increment_marker("marker_2", Field.TRUE_POSITIVES)
        self.markers.increment_marker("marker_1", Field.FALSE_POSITIVES)

        # marker_1 should be the most recent marker in the list
        recent_marker_bytes = self.redis.lindex("markers_list", 0)
        self.assertIsInstance(recent_marker_bytes, bytes)
        recent_marker = recent_marker_bytes.decode()
        self.assertEqual(recent_marker, "marker_1")


if __name__ == "__main__":
    unittest.main()
