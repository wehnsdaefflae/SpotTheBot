from contextlib import contextmanager
from typing import Generator

from nicegui import ui


@contextmanager
def frame(header: bool = True, footer: bool = True) -> Generator[None, None, None]:
    if header:
        with ui.header(elevated=True):
            link_home = ui.link("home", "/")
            label_title = ui.label("Spot the Bot")

    with ui.column() as column:
        yield

    if footer:
        with ui.footer():
            with ui.row() as row:
                label_friends = ui.label("check out friends")
                label_friends.classes("cursor-pointer")
                label_friends.on("click", lambda: ui.open("/friends"))

                label_results = ui.label("check out results")
                label_results.classes("cursor-pointer")
                label_results.on("click", lambda: ui.open("/results"))

                label_about = ui.label("about")
                label_about.classes("cursor-pointer")
                label_about.on("click", lambda: ui.open("/about"))

