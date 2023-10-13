import dataclasses
from enum import Enum


@dataclasses.dataclass
class SecretName:
    name: str = ""


@dataclasses.dataclass(frozen=True)
class Snippet:
    source: str
    content: str
    is_fake: bool


@dataclasses.dataclass(frozen=True)
class StateUpdate:
    true_positives: int
    true_negatives: int
    false_positives: int
    false_negatives: int


@dataclasses.dataclass(frozen=True)
class Face:
    shape: int
    ears: int
    mouth: int
    nose: int
    eyes: int
    hair: int
    accessory: int


@dataclasses.dataclass(frozen=True)
class State:
    last_positives_rate: float
    last_negatives_rate: float


@dataclasses.dataclass(frozen=True)
class Friend:
    db_id: int
    name: str


@dataclasses.dataclass(frozen=True)
class User:
    public_name: str
    secret_name_hash: str
    face: Face
    invited_by_user_id: int
    created_at: float
    state: State

    friends: set[Friend]
    db_id: int = -1


@dataclasses.dataclass(frozen=True)
class Snippet:
    text: str
    source: str
    is_bot: bool
    metadata: tuple[tuple[str, str | int], ...] = tuple()
    db_id: int = -1


class Field(Enum):
    FALSE_POSITIVES = "false_positives"
    FALSE_NEGATIVES = "false_negatives"
    TRUE_POSITIVES = "true_positives"
    TRUE_NEGATIVES = "true_negatives"
