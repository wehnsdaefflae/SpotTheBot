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


def increment_marker(r: redislite.Redis, marker_name: str, field: Field) -> None:
    # increment_marker('repetitive', Field.TRUE_POSITIVE_COUNT)
    # todo: set expiry
    marker_key = f"marker:{marker_name}"
    marker_field_key = f"{marker_key}:{field.value}"
    r.incr(marker_field_key)

    marker_update_key = f"{marker_key}:last_update"
    r.set(marker_update_key, time.time())


def get_marker_value(r: redislite.Redis, marker_name: str, field: Field) -> int:
    # value = get_marker_value('repetitive', Field.TRUE_POSITIVE_COUNT)
    # print(value)  # Outputs: 10
    marker_field_key = f"marker:{marker_name}:{field.value}"
    value = r.get(marker_field_key)
    return int(value) if value else 0


def remove_marker(r: redislite.Redis, marker_name: str) -> None:
    # remove_marker('repetitive')
    marker_keys_pattern = f"marker:{marker_name}:*"
    keys_to_delete = r.keys(marker_keys_pattern)

    # Delete each key
    with r.pipeline() as pipe:
        for key in keys_to_delete:
            r.delete(key)
        pipe.execute()