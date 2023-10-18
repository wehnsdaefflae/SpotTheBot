# coding=utf-8
from nicegui import ui, Client

from src.gui.dummies import DummyContent
from src.dataobjects import ViewCallbacks
from src.gui.page_content_game import GameContent
# from src.gui.page_content_about import about_content
# from src.gui.page_content_friends import friends_content
# from src.gui.page_content_results import results_content
from src.gui.page_content_start import StartContent


class View:
    def __init__(self):
        self.callbacks: ViewCallbacks | None = None

    def set_callbacks(self, callback: ViewCallbacks) -> None:
        self.callbacks = callback

    def setup_routes(self) -> None:
        @ui.page("/")
        async def index_page(client: Client) -> None:
            start_content = StartContent(client, self.callbacks)
            await start_content.create_content()

        @ui.page("/game")
        async def game_page(client: Client) -> None:
            game_content = GameContent(client, self.callbacks)
            await game_content.create_content()

        @ui.page("/friends")
        async def friends_page(client: Client) -> None:
            friends_content = DummyContent(client, self.callbacks)
            await friends_content.create_content()

            # friends_content(self)

        @ui.page("/results")
        async def results_page(client: Client) -> None:
            results_content = DummyContent(client, self.callbacks)
            await results_content.create_content()

            # results_content(self)

        @ui.page("/about")
        async def about_page(client: Client) -> None:
            about_content = DummyContent(client, self.callbacks)
            await about_content.create_content()

            # about_content(self)
