# coding=utf-8
from nicegui import ui, Client, app

from src.gui.dummies import DummyContent
from src.dataobjects import ViewCallbacks
from src.gui.page_content_game import GameContent
from src.gui.page_content_start import StartContent


class View:
    def __init__(self):
        self.callbacks: ViewCallbacks | None = None
        app.add_static_files(url_path="/assets", local_directory="../assets")

    def set_callbacks(self, callback: ViewCallbacks) -> None:
        self.callbacks = callback

    def setup_routes(self) -> None:
        @ui.page("/game")
        async def game_page(client: Client) -> None:
            game_content = GameContent(client, self.callbacks)
            await game_content.create_content()

        @ui.page("/results")
        async def results_page(client: Client) -> None:
            results_content = DummyContent(client, self.callbacks)
            await results_content.create_content()

        @ui.page("/about")
        async def about_page(client: Client) -> None:
            about_content = DummyContent(client, self.callbacks)
            await about_content.create_content()

        @ui.page("/{command}")
        async def hand_in_invitation(client: Client, command: str, value: str) -> None:
            start_content = StartContent(client, self.callbacks)
            if command == "invitation":
                invitation_hash = value
                invitee_id = self.callbacks.get_invitee_id(invitation_hash)
                self.callbacks.remove_invitation_link(invitation_hash)
                start_content.invited_by_id = invitee_id

            await start_content.create_content()

        @ui.page("/")
        async def index_page(client: Client) -> None:
            start_content = StartContent(client, self.callbacks)
            await start_content.create_content()
