import sys

from redis import Redis
from loguru import logger
from redis.client import Pipeline

from src.dataobjects import Field

logger.add(sys.stderr, format="{time} {level} {message}", colorize=True, level="INFO")
logger.add("logs/file_{time}.log", backtrace=True, diagnose=True, rotation="500 MB", level="DEBUG")


class MarkerManager:
    def __init__(self, redis_conf: dict[str, any], max_markers: int) -> None:
        self.redis = Redis(**redis_conf)
        self._max_markers = max_markers
        logger.info("MarkerManager initialized.")

    def evict_markers(self) -> None:
        """Ensures that the total number of markers does not exceed max_markers."""
        current_marker_count = self.redis.zcard("total_count_sortedset")
        if self._max_markers < current_marker_count:
            # Evict least frequently used markers
            markers_to_evict = self.redis.zrange(
                "total_count_sortedset", 0, current_marker_count - self._max_markers - 1
            )

            with self.redis.pipeline() as pipe:
                for marker in markers_to_evict:
                    marker = marker.decode("utf-8")  # Decode for consistency in usage
                    marker_key = f"marker:{marker}"
                    pipe.delete(marker_key)
                    pipe.zrem("total_count_sortedset", marker)
                    pipe.zrem("tp_ratio_sortedset", marker)
                    pipe.zrem("fp_ratio_sortedset", marker)
                pipe.execute()

            logger.info(f"Evicted {len(markers_to_evict)} markers to maintain the max_markers limit.")

    def _update_ratios(self, pipeline: Pipeline, marker_name: str, true_positives: int, false_positives: int) -> None:
        """Updates the ratio scores for a specific marker."""
        positives = true_positives + false_positives

        # Update the ratios if there are any positives
        if 0 >= positives:
            raise ValueError("Positives must be greater than 0.")

        tp_ratio = true_positives / positives
        fp_ratio = false_positives / positives

        pipeline.zadd("tp_ratio_sortedset", {marker_name: tp_ratio})
        pipeline.zadd("fp_ratio_sortedset", {marker_name: fp_ratio})

    def increment_marker(self, marker_name: str, field: Field) -> None:
        """Increments the count for a marker and updates ratios."""
        marker_key = f"marker:{marker_name}"

        # Increment the count and update ratios in an atomic transaction
        with self.redis.pipeline() as pipe:
            true_positives = int(self.redis.hget(marker_key, Field.TRUE_POSITIVES.value) or 0)
            false_positives = int(self.redis.hget(marker_key, Field.FALSE_POSITIVES.value) or 0)

            if field == Field.TRUE_POSITIVES:
                true_positives += 1

            elif field == Field.FALSE_POSITIVES:
                false_positives += 1

            else:
                raise ValueError("Field must be either true positives or false positives.")

            pipe.multi()
            pipe.hincrby(marker_key, field.value, 1)
            pipe.hincrby(marker_key, "total_count", 1)

            self._update_ratios(pipe, marker_name, true_positives, false_positives)  # Pass the counts directly

            pipe.execute()

    def get_markers_by_count(self, n: int) -> list[tuple[str, int]]:
        """Retrieves the n markers with the highest total count."""
        total_count_sortedset = self.redis.zrevrange("total_count_sortedset", 0, n - 1, withscores=True)
        return [(marker.decode('utf-8'), int(score)) for marker, score in total_count_sortedset]

    def get_markers_by_ratio(self, n: int) -> tuple[list[tuple[str, float]], list[tuple[str, float]]]:
        """Retrieves the n markers with the highest true positive and false positive ratios."""
        tp_ratio_sortedset = self.redis.zrevrange("tp_ratio_sortedset", 0, n - 1, withscores=True)
        tp_markers = [(marker.decode('utf-8'), score) for marker, score in tp_ratio_sortedset]

        fp_ratio_sortedset = self.redis.zrevrange("fp_ratio_sortedset", 0, n - 1, withscores=True)
        fp_markers = [(marker.decode('utf-8'), score) for marker, score in fp_ratio_sortedset]

        return tp_markers, fp_markers

    def get_marker_ratios(self, marker_name: str) -> tuple[float, float]:
        """Retrieves the true positive and false positive ratios for a marker."""
        tp_ratio = self.redis.zscore("tp_ratio_sortedset", marker_name)
        fp_ratio = self.redis.zscore("fp_ratio_sortedset", marker_name)

        return tp_ratio, fp_ratio

    def get_marker_counts(self, marker_name: str) -> tuple[int, int]:
        """Retrieves the true positive and false positive counts for a marker."""
        marker_key = f"marker:{marker_name}"
        true_positives = int(self.redis.hget(marker_key, Field.TRUE_POSITIVES.value) or 0)
        false_positives = int(self.redis.hget(marker_key, Field.FALSE_POSITIVES.value) or 0)

        return true_positives, false_positives
