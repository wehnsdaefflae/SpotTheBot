import json
import unittest

from loguru import logger

from src.database.marker_manager import MarkerManager
from src.dataobjects import Field


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

        self.markers = MarkerManager(markers_config, max_markers=self.max_markers)

    def tearDown(self) -> None:
        self.markers.redis.select(self.db_index)
        self.markers.redis.flushdb()

    def test_evict_markers(self):
        # Prepopulate the sorted set with more markers than max_markers
        for i in range(self.max_markers + 5):
            marker_name = f"marker{i}"
            self.markers.redis.zadd("total_count_sortedset", {marker_name: i})

        # Call evict_markers and expect it to evict markers to comply with max_markers limit
        self.markers.evict_markers()

        # Check if the number of markers is now equal to max_markers
        current_marker_count = self.markers.redis.zcard("total_count_sortedset")
        self.assertEqual(current_marker_count, self.max_markers)

    def test_update_ratios(self):
        # Populate Redis with marker data
        marker_name = "test_marker"
        true_positives = 5
        false_positives = 3

        for _ in range(true_positives):
            self.markers.increment_marker(marker_name, Field.TRUE_POSITIVES)

        for _ in range(false_positives):
            self.markers.increment_marker(marker_name, Field.FALSE_POSITIVES)

        tp_ratio, fp_ratio = self.markers.get_marker_ratios(marker_name)
        self.assertEqual(tp_ratio, true_positives / (true_positives + false_positives))
        self.assertEqual(fp_ratio, false_positives / (true_positives + false_positives))

    def test_update_counts(self):
        # Populate Redis with marker data
        marker_name = "test_marker"
        true_positives = 5
        false_positives = 3

        for _ in range(true_positives):
            self.markers.increment_marker(marker_name, Field.TRUE_POSITIVES)

        for _ in range(false_positives):
            self.markers.increment_marker(marker_name, Field.FALSE_POSITIVES)

        _true_positives, _false_positives = self.markers.get_marker_counts(marker_name)
        self.assertEqual(_true_positives, true_positives)
        self.assertEqual(_false_positives, false_positives)

    def test_get_markers_by_count(self):
        # Prepopulate sorted set with markers
        expected_markers = list()
        for i in range(5):
            marker_name = f"marker{i}"
            self.markers.redis.zadd("total_count_sortedset", {marker_name: i})
            expected_markers.append((marker_name, i))

        retrieved_markers = self.markers.get_markers_by_count(5)

        # Assert that retrieved markers match expected markers
        self.assertEqual(retrieved_markers, list(reversed(expected_markers)))

    def test_get_markers_by_ratio(self):
        # Prepopulate sorted sets with markers and their ratios
        for i in range(5):
            marker_name = f"marker{i}"
            tp_score = i / 10
            fp_score = (5 - i) / 10
            self.markers.redis.zadd("tp_ratio_sortedset", {marker_name: tp_score})
            self.markers.redis.zadd("fp_ratio_sortedset", {marker_name: fp_score})

        tp_markers, fp_markers = self.markers.get_markers_by_ratio(5)

        # Assert that the markers with the highest ratios are retrieved
        self.assertEqual(tp_markers[0][0], "marker4")  # Highest TP ratio
        self.assertEqual(fp_markers[0][0], "marker0")  # Highest FP ratio


if __name__ == '__main__':
    unittest.main()
