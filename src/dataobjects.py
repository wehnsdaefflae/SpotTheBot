import dataclasses
import hashlib
import random
import time
from collections import deque, Counter
from enum import Enum
from typing import Callable


def get_random_face_id() -> str:
    number = random.randint(0, 429)  # number of faces
    a = hashlib.shake_128()
    a.update(str(number).encode("utf-8"))
    digest = a.hexdigest(4)
    return digest[::-1]


@dataclasses.dataclass(frozen=True)
class Face:
    source_id: str = dataclasses.field(default_factory=get_random_face_id)


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
    get_friends: Callable[[int], set[Friend]]
    set_user_penalty: Callable[[User, bool], None]
    create_invitation: Callable[[User], str]
    get_invitee_id: Callable[[str], int]
    make_friends: Callable[[int, int], None]
    remove_friendship: Callable[[int, int], None]
    get_user_by_id: Callable[[int], User | None]
    remove_invitation_link: Callable[[str], None]


@dataclasses.dataclass
class Marker:
    label: str

    true_positives: int = 0
    true_negatives: int = 0
    false_positives: int = 0
    false_negatives: int = 0
