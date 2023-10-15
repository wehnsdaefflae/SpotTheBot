from loguru import logger
from nicegui import ui

from src.dataobjects import ViewStorage
from src.gui.frame import create_footer


def about_content(view_storage: ViewStorage) -> None:
    logger.info("About page")

    with ui.header(elevated=True):
        link_home = ui.link("home", "/")
        label_title = ui.label("About")
    text_example = ui.markdown("bla bla bla")
    donate_label = ui.markdown("donate, enter api key, etc")
    api_text = ui.textarea("api key")
    create_footer(view_storage)
