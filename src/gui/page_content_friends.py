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

    async def _invite(self) -> None:
        name_hash = await get_from_local_storage("name_hash")
        if name_hash is None:
            link = "spotthebot.app"
        else:
            invitation_hash = self.callbacks.create_invitation(self.user)
            link = f"spotthebot.app/invitation?value={invitation_hash}"

        with ui.dialog() as dialog, ui.card():
            ui.label(f"Give them this link:")
            # use name hash and friend name to create a link
            ui.label(link)

        dialog.open()

    async def confirm_end_friendship(self, friend_id: int) -> None:
        with ui.dialog() as dialog, ui.card():
            ui.label("Are you sure you want to end this friendship?")
            ui.button("Yes", on_click=lambda: dialog.submit("yes"))
            ui.button("No", on_click=lambda: dialog.submit("no"))

        result = await dialog
        if result == "yes":
            logger.info("Ending friendship")
            self.callbacks.remove_friendship(self.user.db_id, friend_id)
            ui.open("/friends")
        else:
            logger.info("Not ending friendship")

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
                friends = self.callbacks.get_friends(self.user)
                for each_friend in friends:
                    with ui.row():
                        ui.markdown(f"***{each_friend.name.decode()}***")
                        ui.label(str(each_friend.face))
                        ui.button(
                            "Remove",
                            on_click=lambda friend_id=each_friend.db_id: self.confirm_end_friendship(friend_id)
                        )

            invite_button = ui.button("Invite a friend", on_click=self._invite)

