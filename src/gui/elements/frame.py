import hashlib
from contextlib import contextmanager
from typing import Generator

from nicegui import ui

from gui.elements.dialogs import input_dialog
from gui.tools import remove_from_local_storage, set_in_local_storage



@contextmanager
def frame(name_hash: str | None, header: bool = True, footer: bool = True) -> Generator[None, None, None]:
    if header:
        with ui.header(elevated=True) as header:
            header.style("display: flex; justify-content: flex-end;")
            # link_home = ui.link("home", "/")
            # label_title = ui.label("Spot the Bot")

            with ui.row() as row:
                label_results = ui.label("check out results")
                label_results.classes("cursor-pointer")
                label_results.on("click", lambda: ui.open("/results"))

                label_about = ui.label("about")
                label_about.classes("cursor-pointer")
                label_about.on("click", lambda: ui.open("/about"))

            if name_hash is None:
                login_button = ui.button("Log in")

            else:
                label_logout = ui.button("Log out")

    with ui.column() as column:
        yield

