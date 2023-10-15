import dataclasses
import random
import time
from enum import Enum
from typing import Callable


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
    shape: int = int(random.random() * 20)
    ears: int = int(random.random() * 20)
    mouth: int = int(random.random() * 20)
    nose: int = int(random.random() * 20)
    eyes: int = int(random.random() * 20)
    hair: int = int(random.random() * 20)
    accessory: int = int(random.random() * 20)

    def to_tuple(self) -> tuple[int, ...]:
        return self.shape, self.ears, self.mouth, self.nose, self.eyes, self.hair, self.accessory


@dataclasses.dataclass(frozen=True)
class State:
    last_positives_rate: float = .5
    last_negatives_rate: float = .5


@dataclasses.dataclass(frozen=True)
class Friend:
    db_id: int
    name: str


@dataclasses.dataclass(frozen=True)
class User:
    secret_name_hash: str

    face: Face = dataclasses.field(default_factory=Face)
    friends: set[Friend] = dataclasses.field(default_factory=set)
    state: State = dataclasses.field(default_factory=State)
    db_id: int = -1
    invited_by_user_id: int = -1
    created_at: float = dataclasses.field(default_factory=time.time)


@dataclasses.dataclass(frozen=True)
class Snippet:
    text: str
    source: str
    is_bot: bool
    metadata: tuple[tuple[str, str | int], ...] = dataclasses.field(default_factory=tuple)
    db_id: int = -1


class Field(Enum):
    FALSE_POSITIVES = "false_positives"
    FALSE_NEGATIVES = "false_negatives"
    TRUE_POSITIVES = "true_positives"
    TRUE_NEGATIVES = "true_negatives"


@dataclasses.dataclass
class ViewCallbacks:
    get_user: Callable[[str], User]
    create_user: Callable[[User], str]