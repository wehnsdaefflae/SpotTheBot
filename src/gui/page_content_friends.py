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
    async def invite() -> None:
        with ui.dialog() as dialog, ui.card():
            ui.label(f"What's their name?")
            user_name = ui.input("name of friend")
            user_name.on("change", lambda: dialog.submit(user_name.value))

        friend_name = await dialog
        if friend_name is None or len(friend_name) < 1:
            # abort
            return

        name_hash = app.storage.user.get("name_hash", None)
        if name_hash is None:
            # just return app url
            pass

        with ui.dialog() as dialog, ui.card():
            ui.label(f"Give this link to {friend_name} to add them to your friends:")
            # use name hash and friend name to create a link
            ui.label(f"spotthebot.app/invitation/3489fn5f247g25g")

        dialog.open()

    async def create_content(self) -> None:
        logger.info("Game page")

        await self.client.connected()

        # app.on_connect(self.init_tag_count)

        name_hash = await get_from_local_storage("name_hash")
        if name_hash is None:
            ui.open("/")

        self.user = self.callbacks.get_user(name_hash)

        with frame():
            ui.label("Dummy content")
            for each_friend in self.user.friends:
                ui.label(each_friend.name)

            invite_button = ui.button("Invite a friend", on_click=self.invite)

