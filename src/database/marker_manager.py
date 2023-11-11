import sys
from collections import Counter

from redis import Redis
from loguru import logger


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
                    pipe.zrem("correct_ratio_sortedset", marker)
                pipe.execute()

            logger.info(f"Evicted {len(markers_to_evict)} markers to maintain the max_markers limit.")

    def get_most_successful_markers(self, n: int, min_count: int) -> set[tuple[str, float]]:
        """
        Returns a set of n tuples of the form (marker_name, success_ratio) containing
        the markers most often successfully used to identify bots, along with their
        respective success ratios. Only includes markers with at least min_count total uses.
        """
        # Fetch markers with at least min_count uses
        qualified_markers = set(
            marker.decode('utf-8')
            for marker, _ in self.redis.zrangebyscore(
                "total_count_sortedset", min_count, "+inf", withscores=True, start=0, num=n)
        )

        # Fetch top n markers based on success ratio
        successful_markers = self.redis.zrevrangebyscore(
            "correct_ratio_sortedset", 1, 0, withscores=True
        )

        # Filter to include only those with sufficient total uses
        return {
            (decoded, float(score))
            for marker, score in successful_markers
            if (decoded := marker.decode('utf-8')) in qualified_markers
        }

    def get_least_successful_markers(self, n: int, min_count: int) -> set[tuple[str, float]]:
        """
        Returns a set of n tuples of the form (marker_name, success_ratio) containing
        the markers most often unsuccessfully used to identify bots, along with their
        respective failure ratios. Only includes markers with at least min_count total uses.
        """
        # Fetch markers with at least min_count uses
        qualified_markers = set(
            marker.decode('utf-8')
            for marker, _ in self.redis.zrangebyscore(
                "total_count_sortedset", min_count, "+inf", withscores=True, start=0, num=n)
        )

        # Fetch bottom n markers based on success ratio
        unsuccessful_markers = self.redis.zrangebyscore(
            "correct_ratio_sortedset", 0, 1, withscores=True
        )

        # Filter to include only those with sufficient total uses
        return {
            (decoded, 1. - float(score))
            for marker, score in unsuccessful_markers
            if (decoded := marker.decode('utf-8')) in qualified_markers
        }

    def update_markers(self, markers: Counter, correct: bool) -> None:
        correct_int = int(correct)
        with self.redis.pipeline() as pipe:
            for marker_name, marker_count in markers.items():
                marker_key = f"marker:{marker_name}"
                pipe.hincrby(marker_key, "total_count", marker_count)
                pipe.hincrby(marker_key, "correct", correct_int)

            counts = pipe.execute()

            for i, marker_name in enumerate(markers):
                total_count = counts[i * 2]
                correct_count = counts[i * 2 + 1]
                if 0 >= total_count:
                    raise ValueError("Total count of marker must be positive.")

                pipe.zadd("total_count_sortedset", {marker_name: total_count})

                correct_ratio = correct_count / total_count
                pipe.zadd("correct_ratio_sortedset", {marker_name: correct_ratio})

            # Execute the ratio update
            pipe.execute()

    def get_markers_by_count(self, n: int) -> list[tuple[str, int]]:
        total_count_sortedset = self.redis.zrevrange("total_count_sortedset", 0, n - 1, withscores=True)
        return [(marker.decode('utf-8'), int(score)) for marker, score in total_count_sortedset]
