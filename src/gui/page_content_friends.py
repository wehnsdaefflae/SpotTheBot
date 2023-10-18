from nicegui import ui

from src.dataobjects import ViewStorage
from src.gui.elements.frame import create_footer

from loguru import logger


def friends_content(view_storage: ViewStorage) -> None:
    logger.info("Friends page")

    with ui.header(elevated=True):
        link_home = ui.link("home", "/")
        label_title = ui.label("Friends")
    for i in range(10):
        ui.label(f"[ace {i + 1}] [accuracy]")
    create_footer(view_storage)
