from nicegui import ui

from src.gui.frame import create_footer


def friends_content() -> None:
    with ui.header(elevated=True):
        link_home = ui.link("home", "/")
        label_title = ui.label("Friends")
    for i in range(10):
        ui.label(f"[ace {i + 1}] [accuracy]")
    create_footer()
