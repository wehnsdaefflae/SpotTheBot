import sys

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

    def update_markers(self, markers: set[str], correct: bool) -> None:
        correct_int = int(correct)
        with self.redis.pipeline() as pipe:
            for marker_name in markers:
                marker_key = f"marker:{marker_name}"
                pipe.hincrby(marker_key, "total_count", 1)
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

    def _rank_normalized(self, marker_scores: list[tuple[str, float]], minimal_count: int, n: int):
        marker_list = list()
        for marker, score in marker_scores:
            marker_key = f"marker:{marker}"
            total_count = int(self.redis.hget(marker_key, "total_count") or 0)
            if total_count >= minimal_count:
                normalized_score = score / total_count
                marker_list.append((marker, normalized_score))

            if len(marker_list) >= n:
                return marker_list
        return marker_list

    def get_worst_markers(self, n: int, minimal_count: int = 10) -> list[tuple[str, float]]:
        # Retrieve all markers and their scores
        correct_ratio_sortedset = self.redis.zrange("correct_ratio_sortedset", 0, -1, withscores=True)
        incorrect_markers = [(marker.decode('utf-8'), score) for marker, score in correct_ratio_sortedset]
        return self._rank_normalized(incorrect_markers, minimal_count, n)

    def get_best_markers(self, n: int, minimal_count: int = 10) -> list[tuple[str, float]]:
        correct_count_sortedset = self.redis.zrevrange("correct_ratio_sortedset", 0, -1, withscores=True)
        correct_markers = [(marker.decode('utf-8'), score) for marker, score in correct_count_sortedset]
        return self._rank_normalized(correct_markers, minimal_count, n)
