import dataclasses
import random
import time
from collections import deque, Counter
from enum import Enum
from typing import Callable


@dataclasses.dataclass(frozen=True)
class Face:
    shape: int = dataclasses.field(default_factory=lambda: int(random.random() * 20))
    ears: int = dataclasses.field(default_factory=lambda: int(random.random() * 20))
    mouth: int = dataclasses.field(default_factory=lambda: int(random.random() * 20))
    nose: int = dataclasses.field(default_factory=lambda: int(random.random() * 20))
    eyes: int = dataclasses.field(default_factory=lambda: int(random.random() * 20))
    hair: int = dataclasses.field(default_factory=lambda: int(random.random() * 20))
    accessory: int = dataclasses.field(default_factory=lambda: int(random.random() * 20))

    def to_tuple(self) -> tuple[int, ...]:
        return self.shape, self.ears, self.mouth, self.nose, self.eyes, self.hair, self.accessory

    def __str__(self) -> str:
        return f"Shape: {self.shape}\nEars: {self.ears}\nMouth: {self.mouth}\nNose: {self.nose}\nEyes: {self.eyes}\nHair: {self.hair}\nAccessory: {self.accessory}"


@dataclasses.dataclass(frozen=True)
class State:
    precision: float = .5    # tp / (tp + fp), opposite: gullible fp / (tp + fp)
    specificity: float = .5  # tn / (tn + fp), opposite: paranoid fp / (tn + fp)


@dataclasses.dataclass(frozen=True)
class Friend:
    db_id: int
    name: str
    face: Face


@dataclasses.dataclass(frozen=True)
class User:
    secret_name_hash: str
    public_name: str

    penalty: bool = False

    face: Face = dataclasses.field(default_factory=Face)
    state: State = dataclasses.field(default_factory=State)
    db_id: int = -1
    invited_by_user_id: int = -1
    created_at: int = dataclasses.field(default_factory=lambda: int(time.time()))

    recent_snippet_ids: deque[int] = dataclasses.field(default_factory=lambda: deque(maxlen=100))


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


@dataclasses.dataclass(frozen=True)
class ViewCallbacks:
    get_user: Callable[[str], User | None]
    create_user: Callable[[str, Face, str, int], User]
    get_next_snippet: Callable[[User], Snippet]
    update_user_state: Callable[[User, bool, int, int], None]
    update_markers: Callable[[Counter, bool], None]
    most_successful_markers: Callable[[int, int], set[tuple[str, float]]]
    least_successful_markers: Callable[[int, int], set[tuple[str, float]]]
    get_friends: Callable[[User], set[Friend]]
    set_user_penalty: Callable[[User, bool], None]
    create_invitation: Callable[[User], str]
    get_invitee_id: Callable[[str], int]
    make_friends: Callable[[int, int], None]
    remove_friendship: Callable[[int, int], None]


@dataclasses.dataclass
class Marker:
    label: str

    true_positives: int = 0
    true_negatives: int = 0
    false_positives: int = 0
    false_negatives: int = 0
