import hashlib
from contextlib import contextmanager
from typing import Generator

from nicegui import ui

from src.gui.elements.dialogs import input_dialog
from src.gui.tools import remove_from_local_storage, set_in_local_storage


async def logout() -> None:
    with ui.dialog().props("persistent") as dialog, ui.card():
        ui.label(
            "Are you sure you want to log out? If you want to restore it, you need to know your secret name."
        )
        with ui.row() as button_row:
            ui.button("yes", on_click=lambda: dialog.submit("yes"))
            ui.button("no", on_click=lambda: dialog.submit("no"))

    result = await dialog
    if result == "yes":
        await remove_from_local_storage("name_hash")

        ui.open("/")


async def login() -> None:
    secret_name = await input_dialog("Enter your secret name.")
    name_hash = hashlib.sha256(secret_name.encode()).hexdigest()
    await set_in_local_storage("name_hash", name_hash)
    ui.open("/")


@contextmanager
def frame(name_hash: str | None, header: bool = True, footer: bool = True) -> Generator[None, None, None]:
    if header:
        with ui.header(elevated=True):
            # link_home = ui.link("home", "/")
            # label_title = ui.label("Spot the Bot")

            if name_hash is None:
                login_button = ui.button("Log in", on_click=login)

            else:
                label_logout = ui.button("Log out", on_click=logout)

    with ui.column() as column:
        yield

    if footer:
        with ui.footer():
            with ui.row() as row:
                label_results = ui.label("check out results")
                label_results.classes("cursor-pointer")
                label_results.on("click", lambda: ui.open("/results"))

                label_about = ui.label("about")
                label_about.classes("cursor-pointer")
                label_about.on("click", lambda: ui.open("/about"))

