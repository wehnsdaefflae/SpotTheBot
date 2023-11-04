import json
import unittest

from loguru import logger

from src.database.marker_manager import MarkerManager


class TestMarkers(unittest.TestCase):

    def setUp(self) -> None:
        # Remove any existing test database files
        logger.info(f"Starting up marker database tests.")

        # Initialize MarkerManager with a redislite Redis instance
        with open("../../config.json", mode="r") as config_file:
            config = json.load(config_file)

        self.max_markers = 10
        database_config = config.pop("redis")
        markers_config = database_config.pop("markers_database")
        markers_config["db"] += 10  # test index
        self.db_index = markers_config["db"]

        self.marker_manager = MarkerManager(markers_config, max_markers=self.max_markers)
        self.redis = self.marker_manager.redis
        self.redis.flushdb()  # Start with a clean database for each test

    def tearDown(self) -> None:
        self.marker_manager.redis.select(self.db_index)
        self.marker_manager.redis.flushdb()

    def test_evict_markers(self):
        # Add markers to reach the max limit
        for i in range(self.max_markers + 5):  # Add more markers than max
            self.marker_manager.update_markers({f"marker_{i}"}, True)

        self.marker_manager.evict_markers()

        # There should be only max_markers left
        self.assertEqual(self.redis.zcard("total_count_sortedset"), self.max_markers)

        # Check that the lowest scored markers were evicted
        markers = self.redis.zrange("total_count_sortedset", 0, -1)
        markers = {marker.decode('utf-8') for marker in markers}
        self.assertNotIn("marker_0", markers)  # The first marker should be evicted
        self.assertIn(f"marker_{self.max_markers + 4}", markers)  # The last one should still be there

    def test_update_markers_correct(self):
        marker_names = {'marker1', 'marker2'}
        self.marker_manager.update_markers(marker_names, True)

        # Check if the markers have been updated correctly
        for marker_name in marker_names:
            marker_key = f"marker:{marker_name}"
            self.assertEqual(int(self.redis.hget(marker_key, "total_count")), 1)
            self.assertEqual(int(self.redis.hget(marker_key, "correct")), 1)

        # Check the correct_ratio_sortedset
        for marker_name in marker_names:
            score = self.redis.zscore("correct_ratio_sortedset", marker_name)
            self.assertEqual(score, 1.0)

    def test_update_markers_incorrect(self):
        marker_names = {'marker1', 'marker2'}
        self.marker_manager.update_markers(marker_names, False)

        # Check if the markers have been updated correctly
        for marker_name in marker_names:
            marker_key = f"marker:{marker_name}"
            self.assertEqual(int(self.redis.hget(marker_key, "total_count")), 1)
            self.assertEqual(int(self.redis.hget(marker_key, "correct")), 0)

        # Check the correct_ratio_sortedset
        for marker_name in marker_names:
            score = self.redis.zscore("correct_ratio_sortedset", marker_name)
            self.assertEqual(score, 0.0)  # The score should be 0.0 for incorrect

    def test_get_markers_by_count(self):
        # Add some markers with their counts
        for i in range(5):
            for _ in range(i+1):
                self.marker_manager.update_markers({f"marker:{i}"}, True)

        # Get the top n markers
        markers = self.marker_manager.get_markers_by_count(3)

        # Check if the top 3 markers are returned with the correct scores
        expected_markers = [(f"marker:{i}", i + 1) for i in reversed(range(2, 5))]
        self.assertEqual(markers, expected_markers)

    def test_get_worst_markers(self):
        for i in range(10):
            self.marker_manager.update_markers({f"marker:{i}"}, i % 2 == 0)

        # Get the worst n markers
        markers = self.marker_manager.get_worst_markers(3, minimal_count=1)

        # Check if the worst 3 markers are returned
        expected_markers = [(f"marker:{i}", 0.) for i in range(1, 10, 2)]
        self.assertTrue(all(each_expected_marker in expected_markers for each_expected_marker in markers))

    def test_get_best_markers(self):
        for i in range(10):
            self.marker_manager.update_markers({f"marker:{i}"}, i % 2 == 0)

        # Get the best n markers
        markers = self.marker_manager.get_best_markers(3, minimal_count=1)

        # Check if the best 3 markers are returned
        expected_markers = [(f"marker:{i}", 1.) for i in range(2, 10, 2)]
        self.assertTrue(all(each_expected_marker in expected_markers for each_expected_marker in markers))


if __name__ == '__main__':
    unittest.main()
