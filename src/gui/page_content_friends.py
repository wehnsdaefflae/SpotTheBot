from nicegui import ui, Client, app

from loguru import logger

from src.gui.elements.frame import frame
from src.dataobjects import ViewCallbacks
from src.gui.elements.content_class import ContentPage
from src.gui.tools import get_from_local_storage


class FriendsContent(ContentPage):
    def __init__(self, client: Client, callbacks: ViewCallbacks) -> None:
        super().__init__(client, callbacks)
        self.user = None

    @staticmethod
    async def _invite() -> None:
        name_hash = app.storage.user.get("name_hash", None)
        if name_hash is None:
            link = "spotthebot.app"
        else:
            link = "spotthebot.app/invitation/3489fn5f247g25g"

        with ui.dialog() as dialog, ui.card():
            ui.label(f"Give them this link:")
            # use name hash and friend name to create a link
            ui.label(link)

        dialog.open()

    async def create_content(self) -> None:
        logger.info("Game page")

        await self.client.connected()

        # app.on_connect(self.init_tag_count)

        name_hash = await get_from_local_storage("name_hash")
        if name_hash is None:
            ui.open("/")

        self.user = self.callbacks.get_user(name_hash)
        if self.user is None:
            ui.open("/")

        with frame():
            ui.label("Dummy content")
            with ui.column():
                for each_friend in self.callbacks.get_friends(self.user):
                    with ui.row():
                        ui.label(each_friend.name)
                        ui.button("Remove", on_click=lambda: None)

            invite_button = ui.button("Invite a friend", on_click=self._invite)

