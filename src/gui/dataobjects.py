import dataclasses


@dataclasses.dataclass
class SecretName:
    name: str = ""


@dataclasses.dataclass(frozen=True)
class Snippet:
    source: str
    content: str
    is_fake: bool
