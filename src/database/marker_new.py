import sys

from redis import Redis
from loguru import logger

from src.dataobjects import Field, Marker

logger.add(sys.stderr, format="{time} {level} {message}", colorize=True, level="INFO")
logger.add("logs/file_{time}.log", backtrace=True, diagnose=True, rotation="500 MB", level="DEBUG")


class Markers:
    def __init__(self, redis_conf: dict[str, str]) -> None:
        self.redis = Redis(**redis_conf)
        logger.info("Markers initialized.")

    def update_marker(self, marker_name: str, field: Field, value: int = 1) -> None:
        marker_key = f"marker:{marker_name}"
        self.redis.hincrby(marker_key, field.value, value)

    def get_marker(self, marker_name: str) -> Marker:
        marker_key = f"marker:{marker_name}"
        result = self.redis.hgetall(marker_key)
        data = {
            key.decode(): value.decode()
            for key, value in result.items()
        }

        return Marker(
            marker_name,
            int(data.pop("true_positives")), int(data.pop("false_positives")),
            int(data.pop("false_negatives")), int(data.pop("true_negatives"))
        )