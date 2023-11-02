# coding=utf-8
import hashlib
import random

from nicegui import ui, app, Client

from src.dataobjects import User, ViewCallbacks
from src.gui.elements.content_class import ContentPage
from src.gui.elements.dialogs import persistent_dialog
from src.gui.elements.face import show_face
from src.gui.tools import download_vcard, get_from_local_storage, set_in_local_storage
from src.gui.elements.frame import frame
from src.tools.names import generate_name
from loguru import logger


class StartContent(ContentPage):
    def __init__(self, client: Client, callbacks: ViewCallbacks) -> None:
        super().__init__(client, callbacks)
        self.secret_name = None
        self.user = None

    async def make_user(self) -> User:
        name_seed = tuple(random.random() for _ in range(7))
        self.secret_name = generate_name(name_seed)
        name_hash = hashlib.sha256(self.secret_name.encode()).hexdigest()
        return User(name_hash)

    async def set_user(self) -> None:
        await self.client.connected()
        name_hash = await get_from_local_storage("name_hash")
        if name_hash is None:
            # no user yet
            self.user = await self.make_user()

        else:
            # user in local storage
            try:
                # user retrieved
                self.user = self.callbacks.get_user(name_hash)

            except KeyError as e:
                # no user for hash in local storage
                logger.error(e)
                await persistent_dialog("Sorry, there's no user with that identity. Did you mistype?")
                self.user = await self.make_user()

    async def start_game(self) -> None:
        if self.user.db_id < 0:
            self.callbacks.create_user(self.user)
            await persistent_dialog("Keep the following file safe!")
            source_path, target_path = download_vcard(self.secret_name)
            ui.download(source_path, target_path)
            await set_in_local_storage("identity_file", source_path)
            await set_in_local_storage("name_hash", self.user.secret_name_hash)
            self.secret_name = None
            self.user = None

        ui.open("/game")

    @staticmethod
    async def invite() -> None:
        with ui.dialog() as dialog, ui.card():
            ui.label(f"What's their name?")
            user_name = ui.input("name of friend")
            user_name.on("change", lambda: dialog.submit(user_name.value))

        friend_name = await dialog

        if friend_name is None or len(friend_name) < 1:
            # generate link without name
            pass

        name_hash = app.storage.user.get("name_hash", None)
        if name_hash is None:
            # just return app url
            pass

        with ui.dialog() as dialog, ui.card():
            ui.label(f"Give this link to {friend_name} to add them to your friends:")
            # use name hash and friend name to create a link
            ui.label(f"spotthebot.app/invite?=3489fn5f247g25g")

        dialog.open()

    def change_user(self, secret_identity: str) -> None:
        name_hash = hashlib.sha256(secret_identity.encode()).hexdigest()
        set_in_local_storage("name_hash", name_hash)
        ui.open("/")

    async def create_content(self) -> None:
        logger.info("Start page")
        await self.set_user()

        with frame() as _frame:
            with ui.column() as column:
                title_label = ui.label("Look out for robots!")
                title_label.classes("text-h4 font-bold text-grey-8")

                with ui.row():
                    with ui.column():
                        ui.markdown("What robots sound like:")
                        # most true positives among positives
                        # Attributes most commonly and correctly identified by users as robot-like
                        for i in range(4):
                            each_indicator_label = ui.label(f"[indicator {i + 1}] [accuracy]")

                    with ui.column():
                        ui.markdown("What humans **do not** sound like:")
                        # most false positives among negatives
                        # Attributes users most commonly mistake as robot-like in human-written text
                        for i in range(4):
                            each_indicator_label = ui.label(f"[indicator {i + 1}] [accuracy]")

                face_element = show_face(self.user.face)

                ui.label("this isn't you?")
                identity_input = ui.input("take on your secret identity")
                identity_input.on("change", lambda: self.change_user(identity_input.value))

                button_start = ui.button("SPOT THE BOT", on_click=self.start_game)

                ui.label(f"or")

                invite_button = ui.button("Invite a friend", on_click=self.invite)
