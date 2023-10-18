from contextlib import contextmanager
from typing import Generator

from nicegui import ui, app

from src.gui.tools import remove_from_local_storage


async def logout() -> None:
    with ui.dialog().props("persistent") as dialog, ui.card():
        ui.label("Are you sure you want to change identity? If you want to restore it, you need to know your name.")
        with ui.row() as button_row:
            ui.button("yes", on_click=lambda: dialog.submit("yes"))
            ui.button("no", on_click=lambda: dialog.submit("no"))

    result = await dialog
    if result == "yes":
        await remove_from_local_storage("name_hash")

        ui.open("/")


@contextmanager
def frame(header: bool = True, footer: bool = True) -> Generator[None, None, None]:
    if header:
        with ui.header(elevated=True):
            link_home = ui.link("home", "/")
            label_title = ui.label("Spot the Bot")

    with ui.column():
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

                label_logout = ui.label("change identity")
                label_logout.classes("cursor-pointer")
                label_logout.on("click", logout)

