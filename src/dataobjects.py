from __future__ import annotations

import dataclasses
import random
import time
from collections import deque, Counter
from typing import Callable


def get_random_face_id() -> str:
    number = random.randint(0, 220)  # number of faces
    return f"{number:04d}"


@dataclasses.dataclass(frozen=True)
class Face:
    source_id: str = dataclasses.field(default_factory=get_random_face_id)


@dataclasses.dataclass(frozen=True)
class Friend:
    db_id: int
    name: str
    face: Face
    anger: float
    sadness: float


@dataclasses.dataclass(frozen=True)
class User:
    secret_name_hash: str
    public_name: str

    penalty: bool = False

    face: Face = dataclasses.field(default_factory=Face)
    true_positives: float = 0
    true_negatives: float = 0
    false_positives: float = 0
    false_negatives: float = 0

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


@dataclasses.dataclass(frozen=True)
class ViewCallbacks:
    get_user: Callable[[str], User | None]
    create_user: Callable[[str, Face, str, int], User]
    get_next_snippet: Callable[[User], Snippet]
    update_user_state: Callable[[User, float, float, float, float], None]
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


@dataclasses.dataclass
class BinaryStats:
    true_positives: float = 0.
    true_negatives: float = 0.
    false_positives: float = 0.
    false_negatives: float = 0.

    def clear(self) -> None:
        self.true_positives = 0.
        self.true_negatives = 0.
        self.false_positives = 0.
        self.false_negatives = 0.

    @property
    def actually_positive(self) -> float:
        return self.true_positives + self.false_negatives

    @property
    def actually_negative(self) -> float:
        return self.true_negatives + self.false_positives

    @property
    def classified_positive(self) -> float:
        return self.true_positives + self.false_positives

    @property
    def classified_negative(self) -> float:
        return self.true_negatives + self.false_negatives

    @property
    def total(self) -> float:
        return self.actually_positive + self.actually_negative

    @property
    def accuracy(self) -> float:
        if 0. >= self.total:
            return 0.
        return (self.true_positives + self.true_negatives) / self.total

    @property
    def precision(self) -> float:
        if 0. >= self.classified_positive:
            return 0.
        return self.true_positives / self.classified_positive

    @property
    def recall(self) -> float:
        if 0. >= self.actually_positive:
            return 0.
        return self.true_positives / self.actually_positive

    @property
    def true_positive_rate(self) -> float:
        if 0. >= self.actually_positive:
            return 0.
        return self.true_positives / self.actually_positive

    @property
    def true_negative_rate(self) -> float:
        if 0. >= self.actually_negative:
            return 0.
        return self.true_negatives / self.actually_negative

    @property
    def false_positive_rate(self) -> float:
        if 0. >= self.actually_negative:
            return 0.
        return self.false_positives / self.actually_negative

    @property
    def false_negative_rate(self) -> float:
        if 0. >= self.actually_positive:
            return 0.
        return self.false_negatives / self.actually_positive

    @property
    def f1(self) -> float:
        precision_plus_recall = self.precision + self.recall
        if 0. >= precision_plus_recall:
            return 0.
        return 2. * self.precision * self.recall / precision_plus_recall

    def __str__(self) -> str:
        return (
            f"tp: {self.true_positives:.2f}, "
            f"tn: {self.true_negatives:.2f}, "
            f"fp: {self.false_positives:.2f}, "
            f"fn: {self.false_negatives:.2f}"
        )

    def __add__(self, other: BinaryStats) -> BinaryStats:
        return BinaryStats(
            self.true_positives + other.true_positives,
            self.true_negatives + other.true_negatives,
            self.false_positives + other.false_positives,
            self.false_negatives + other.false_negatives
        )

    def __iadd__(self, other: BinaryStats) -> BinaryStats:
        self.true_positives += other.true_positives
        self.true_negatives += other.true_negatives
        self.false_positives += other.false_positives
        self.false_negatives += other.false_negatives
        return self

    def __mul__(self, other: float) -> BinaryStats:
        return BinaryStats(
            self.true_positives * other,
            self.true_negatives * other,
            self.false_positives * other,
            self.false_negatives * other
        )

    def __imul__(self, other: float) -> BinaryStats:
        self.true_positives *= other
        self.true_negatives *= other
        self.false_positives *= other
        self.false_negatives *= other
        return self

    def __rmul__(self, other: float) -> BinaryStats:
        return self * other

    def __truediv__(self, other: float) -> BinaryStats:
        return BinaryStats(
            self.true_positives / other,
            self.true_negatives / other,
            self.false_positives / other,
            self.false_negatives / other
        )

    def __itruediv__(self, other: float) -> BinaryStats:
        self.true_positives /= other
        self.true_negatives /= other
        self.false_positives /= other
        self.false_negatives /= other
        return self

    def __rtruediv__(self, other: float) -> BinaryStats:
        return self / other
