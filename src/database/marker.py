import subprocess
import sys

import loguru
import redislite.patch
redislite.patch.patch_redis()

from redis import Redis

from loguru import logger

from src.dataobjects import Field

logger.add(sys.stderr, format="{time} {level} {message}", colorize=True, level="INFO")
logger.add("logs/file_{time}.log", backtrace=True, diagnose=True, rotation="500 MB", level="DEBUG")


class Markers:
    def __init__(self, redis: Redis | None = None, max_markers: int = 100, debugging: bool = False) -> None:
        db_index = 2
        self.redis = redis or Redis("../database/spotthebot.rdb", db=db_index)
        loguru.logger.info(
            f"Markers initialized. "
            f"`qredis -s {self.redis.connection_pool.connection_kwargs['path']} -n {db_index}`"
        )
        if debugging:
            subprocess.Popen(["qredis", "-s", self.redis.connection_pool.connection_kwargs['path'], "-n", str(db_index)])

        self.max_markers = max_markers

    def _remove_older_markers(self) -> None:
        """Removes markers that are beyond the limit."""
        markers_to_remove = self.redis.lrange("markers_list", self.max_markers, -1)

        with self.redis.pipeline() as pipe:
            for each_marker_name in markers_to_remove:
                each_decoded = each_marker_name.decode()
                each_marker_key = f"marker:{each_decoded}"
                pipe.delete(each_marker_key)

            pipe.ltrim("markers_list", 0, self.max_markers - 1)
            pipe.execute()

    def _update_marker_list(self, marker_name: str) -> None:
        """Updates the marker list to reflect recent access."""
        # Add marker to the front of the list
        self.redis.lpush("markers_list", marker_name)

        # Remove older markers if the list had grown beyond the limit
        self._remove_older_markers()

    def increment_marker(self, marker_name: str, field: Field) -> None:
        marker_key = f"marker:{marker_name}"
        self.redis.hincrby(marker_key, field.value, 1)

        # Update marker list
        self._update_marker_list(marker_name)

    def get_marker_value(self, marker_name: str, field: Field) -> int:
        marker_key = f"marker:{marker_name}"
        value = self.redis.hget(marker_key, field.value)
        return int(value) if value else 0

    def remove_marker(self, marker_name: str) -> None:
        marker_key = f"marker:{marker_name}"

        # Delete the hash and remove the marker from the list
        with self.redis.pipeline() as pipe:
            pipe.delete(marker_key)
            pipe.lrem("markers_list", 0, marker_name)
            pipe.execute()
