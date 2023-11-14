# coding=utf-8
import hashlib
import random

from nicegui import ui, Client

from src.dataobjects import ViewCallbacks, Face
from src.gui.elements.content_class import ContentPage
from src.gui.elements.dialogs import info_dialog, input_dialog
from src.gui.elements.face import show_face
from src.gui.tools import download_vcard, get_from_local_storage, set_in_local_storage, remove_from_local_storage
from src.gui.elements.frame import frame
from src.tools.names import generate_name
from loguru import logger


class StartContent(ContentPage):
    def __init__(self, client: Client, callbacks: ViewCallbacks) -> None:
        super().__init__(client, callbacks)
        self.face = None
        self.logged_in_user_name = None
        self.invited_by_id = None

    async def set_user(self) -> None:
        name_hash = await get_from_local_storage("name_hash")
        if name_hash is None:
            self.face = Face()

        else:
            user = self.callbacks.get_user(name_hash)
            if user is None:
                msg = "Sorry, there's no user with that identity. Did you mistype?"
                await remove_from_local_storage("name_hash")

                logger.error(msg)
                await info_dialog(msg)

                self.face = Face()

            else:
                self.face = user.face
                self.logged_in_user_name = user.public_name

    async def _start_game(self) -> None:
        if self.logged_in_user_name is None:
            public_name = await input_dialog("Enter your name and keep the following file safe.")
            name_seed = tuple(random.random() for _ in range(7))
            secret_name = generate_name(name_seed)
            invited_by_user_id = -1
            user = self.callbacks.create_user(secret_name, self.face, public_name, invited_by_user_id)

            if self.invited_by_id is not None:
                self.callbacks.make_friends(user.db_id, self.invited_by_id)

            source_path, target_path = download_vcard(secret_name, public_name)
            ui.download(source_path, target_path)
            await set_in_local_storage("identity_file", source_path)
            await set_in_local_storage("name_hash", user.secret_name_hash)

        ui.open("/game")

    def change_user(self, secret_identity: str) -> None:
        name_hash = hashlib.sha256(secret_identity.encode()).hexdigest()
        set_in_local_storage("name_hash", name_hash)
        ui.open("/")

    async def create_content(self) -> None:
        logger.info("Start page")
        await self.client.connected()

        await self.set_user()

        with frame() as _frame:
            with ui.column() as column:
                if self.logged_in_user_name is None:
                    if self.invited_by_id is None:
                        invited = ""
                    else:
                        invitee = self.callbacks.get_user_by_id(self.invited_by_id)
                        invited = f" {invitee.public_name} invited"
                    ui.label(f"Oh...{invited} a new face!")
                else:
                    ui.label(f"Welcome back, {self.logged_in_user_name}!")

                title_label = ui.label("Look out for robots!")
                title_label.classes("text-h4 font-bold text-grey-8")

                ui.markdown("Consider the following hints:")

                with ui.row():
                    with ui.column():
                        # most true positives among positives
                        # Attributes most commonly and correctly identified by users as robot-like
                        good_markers = sorted(
                            self.callbacks.most_successful_markers(4, 10),
                            key=lambda x: x[1], reverse=True
                        )
                        for i, (each_marker, each_score) in enumerate(good_markers):
                            each_indicator_label = ui.markdown(
                                f"{each_score:.0%} of AI texts sound ***{each_marker}***"
                            )

                    with ui.column():
                        # most false positives among negatives
                        # Attributes users most commonly mistake as robot-like in human-written text
                        bad_markers = sorted(
                            self.callbacks.least_successful_markers(4, 10),
                            key=lambda x: x[1], reverse=True
                        )
                        for i, (each_marker, each_score) in enumerate(bad_markers):
                            each_indicator_label = ui.markdown(
                                f"{each_score:.0%} of human texts **don't** sound ***{each_marker}***"
                            )

                face_element = show_face(self.face)

                ui.label("this isn't you?")
                identity_input = ui.input("take on your secret identity")
                identity_input.on("change", lambda: self.change_user(identity_input.value))

                button_start = ui.button("SPOT THE BOT", on_click=self._start_game)
