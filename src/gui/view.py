# coding=utf-8
from nicegui import ui

from src.gui.page_content_about import about_content
from src.dataobjects import ViewCallbacks, ViewStorage
from src.gui.page_content_friends import friends_content
from src.gui.page_content_game import game_content
from src.gui.page_content_results import results_content
from src.gui.page_content_start import start_content


class View:
    def __init__(self):
        self.callbacks: ViewCallbacks | None = None
        self.storage: ViewStorage = ViewStorage()

    def set_callbacks(self, callback: ViewCallbacks) -> None:
        self.callbacks = callback

    def setup_routes(self) -> None:
        @ui.page("/friends")
        def friends_page() -> None:
            friends_content()

        @ui.page("/results")
        def results_page() -> None:
            results_content()

        @ui.page("/about")
        def about_page() -> None:
            about_content()

        @ui.page("/game")
        def game_page() -> None:
            game_content(self.storage)

        @ui.page("/")
        def index_page() -> None:
            start_content(self.storage, self.callbacks)
