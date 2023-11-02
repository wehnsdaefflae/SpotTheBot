import sys

from redis import Redis
from loguru import logger

from src.dataobjects import Field

logger.add(sys.stderr, format="{time} {level} {message}", colorize=True, level="INFO")
logger.add("logs/file_{time}.log", backtrace=True, diagnose=True, rotation="500 MB", level="DEBUG")


class Markers:
    def __init__(self, redis_conf: dict[str, str]) -> None:
        self.redis = Redis(**redis_conf)
        logger.info("Markers initialized.")

    def _update_ratios(self, marker_name: str) -> None:
        """Public method to update ratios for a specific marker."""

        marker_key = f"marker:{marker_name}"
        true_positives = int(self.redis.hget(marker_key, "true_positives") or 0)
        false_negatives = int(self.redis.hget(marker_key, "false_negatives") or 0)
        false_positives = int(self.redis.hget(marker_key, "false_positives") or 0)
        true_negatives = int(self.redis.hget(marker_key, "true_negatives") or 0)

        positives = true_positives + false_negatives
        negatives = false_positives + true_negatives

        tp_ratio = true_positives / positives if positives != 0 else 0
        fp_ratio = false_positives / negatives if negatives != 0 else 0

        self.redis.zadd("tp_ratio_sortedset", {marker_name: tp_ratio})
        self.redis.zadd("fp_ratio_sortedset", {marker_name: fp_ratio})

    def increment_marker(self, marker_name: str, field: Field) -> None:
        marker_key = f"marker:{marker_name}"
        self.redis.hincrby(marker_key, field.value, 1)
        self._update_ratios(marker_name)

    def get_marker_value(self, marker_name: str, field: Field) -> int:
        marker_key = f"marker:{marker_name}"
        value = self.redis.hget(marker_key, field.value)
        return int(value) if value else 0

    def remove_marker(self, marker_name: str) -> None:
        marker_key = f"marker:{marker_name}"

        # Delete the hash and remove the marker from the sorted sets
        with self.redis.pipeline() as pipe:
            pipe.delete(marker_key)
            pipe.zrem("tp_ratio_sortedset", marker_name)
            pipe.zrem("fp_ratio_sortedset", marker_name)
            pipe.execute()

    def get_top_n_markers(self, n: int) -> dict:
        """
        Retrieves the top n markers based on their ratios.

        Returns:
            A dictionary with the following structure:
            {
                "tp_ratio": [(marker_name1, ratio1), (marker_name2, ratio2), ...],
                "fp_ratio": [(marker_name1, ratio1), (marker_name2, ratio2), ...]
            }
        """
        top_tp_markers = self.redis.zrevrange("tp_ratio_sortedset", 0, n - 1, withscores=True)
        top_fp_markers = self.redis.zrevrange("fp_ratio_sortedset", 0, n - 1, withscores=True)

        return {
            "tp_ratio": top_tp_markers,
            "fp_ratio": top_fp_markers
        }
