from contextlib import contextmanager
from typing import Generator
from nicegui import ui


@contextmanager
def frame() -> Generator[None, None, None]:
    with ui.header():
        ui.label("header")
    with ui.column():
        yield
    with ui.footer():
        ui.label("footer")


@ui.page("/")
def index_page() -> None:
    with frame():
        ui.label("content")


def main() -> None:
    ui.run(title="MWE")


if __name__ in {"__main__", "__mp_main__"}:
    main()
