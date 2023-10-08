import sys
import time
from enum import Enum

import redislite
from loguru import logger

logger.add(sys.stderr, format="{time} {level} {message}", colorize=True, level="INFO")
logger.add("file_{time}.log", backtrace=True, diagnose=True, rotation="500 MB", level="DEBUG")


class Field(Enum):
    FALSE_POSITIVES = "false_positives"
    FALSE_NEGATIVES = "false_negatives"
    TRUE_POSITIVES = "true_positives"
    TRUE_NEGATIVES = "true_negatives"


class Markers:
    def __init__(self, redis: redislite.Redis, expiration_seconds: int = 60 * 60 * 24 * 7 * 30 * 6) -> None:
        self.redis = redis
        self.expiration_seconds = expiration_seconds

    def increment_marker(self, marker_name: str, field: Field) -> None:
        # increment_marker('repetitive', Field.TRUE_POSITIVE_COUNT)
        marker_key = f"marker:{marker_name}"
        marker_field_key = f"{marker_key}:{field.value}"
        self.redis.incr(marker_field_key)
        self.redis.expire(marker_field_key, self.expiration_seconds)

    def get_marker_value(self, marker_name: str, field: Field) -> int:
        # value = get_marker_value('repetitive', Field.TRUE_POSITIVE_COUNT)
        # print(value)  # Outputs: 10
        marker_field_key = f"marker:{marker_name}:{field.value}"
        value = self.redis.get(marker_field_key)
        return int(value) if value else 0

    def remove_marker(self, marker_name: str) -> None:
        # remove_marker('repetitive')
        marker_keys_pattern = f"marker:{marker_name}:*"
        keys_to_delete = self.redis.keys(marker_keys_pattern)

        # Delete each key
        with self.redis.pipeline() as pipe:
            for key in keys_to_delete:
                self.redis.delete(key)
            pipe.execute()
