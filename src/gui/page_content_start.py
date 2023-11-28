# coding=utf-8
import hashlib
import random

from nicegui import ui, Client

from src.dataobjects import ViewCallbacks, Face
from src.gui.elements.content_class import ContentPage
from src.gui.elements.dialogs import info_dialog, input_dialog, option_dialog
from src.gui.elements.face import show_face
from src.gui.tools import download_vcard, get_from_local_storage, set_in_local_storage, remove_from_local_storage
from src.gui.elements.frame import frame
from src.tools.faces.names import generate_name
from loguru import logger


async def logout() -> None:
    with ui.dialog().props("persistent") as dialog, ui.card():
        ui.label(
            "Are you sure you want to log out? If you want to restore it, you need to know your secret name."
        )
        with ui.row() as button_row:
            ui.button("yes", on_click=lambda: dialog.submit("yes"))
            ui.button("no", on_click=lambda: dialog.submit("no"))

    result = await dialog
    if result == "yes":
        await remove_from_local_storage("name_hash")

        ui.open("/")


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
            await info_dialog(
                "Tutorial: Please safe the following file. End each game using the \"quit\" button to prevent penalty."
            )
            public_name = await input_dialog("Enter your name and keep the following file safe.")
            name_seed = tuple(random.random() for _ in range(7))
            secret_name = generate_name(name_seed)
            invited_by_user_id = -1
            user = self.callbacks.create_user(secret_name, self.face, public_name, invited_by_user_id)

            if self.invited_by_id is not None:
                self.callbacks.make_friends(user.db_id, self.invited_by_id)

            source_path, target_path = download_vcard(secret_name, public_name, self.face.source_id)
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
            with ui.column() as top_column:
                top_column.classes("items-center justify-center h-full w-full")

                title_label = ui.label("Spot the Bot")
                title_label.classes("text-h2")

                with ui.row() as main_row:
                    main_row.classes("items-center justify-center")
                    # main_row.classes("items-center")

                    with ui.column() as column:
                        column.classes("items-center justify-center")
                        if self.logged_in_user_name is None:
                            if self.invited_by_id is None:
                                ui.label(f"Oh... ein neues Gesicht.")
                            else:
                                invitee = self.callbacks.get_user_by_id(self.invited_by_id)
                                invited = f" {invitee.public_name} invited"
                                ui.label(f"So, Du kommst also von {invitee.public_name}.")
                        else:
                            if self.invited_by_id is None:
                                ui.label(f"Willkommen zurück, {self.logged_in_user_name}!")
                            else:
                                invitee = self.callbacks.get_user_by_id(self.invited_by_id)

                                option = await option_dialog(
                                    f"Willst Du mit {invitee.public_name} befreundet sein?",
                                    ["ja", "nein"]
                                )
                                if option == "ja":
                                    name_hash = await get_from_local_storage("name_hash")
                                    user = self.callbacks.get_user(name_hash)
                                    self.callbacks.make_friends(
                                        self.invited_by_id,
                                        user.db_id
                                    )

                        face_element = show_face(self.face)
                        face_element.classes("w-64 justify-center")
                        # face_element.classes("w-64 justify-center")

                    with ui.column() as mid_column:
                        mid_column.classes("items-center justify-center")
                        button_start = ui.button("Start!", on_click=self._start_game)

                        ui.label("oder")

                        name_hash = await get_from_local_storage("name_hash")
                        if name_hash is None:
                            identity_input = ui.input("Wechsel Deine Identität")
                            identity_input.on("change", lambda: self.change_user(identity_input.value))

                        else:
                            label_logout = ui.button("Log out", on_click=logout)

            with ui.column() as bottom_column:
                bottom_column.classes("items-center justify-center h-full w-full")
                hints = ui.markdown("Achte auf:")
                hints.classes("text-h3")

                with ui.row() as pos_neg_row:
                    pos_neg_row.classes("items-center justify-center")
                    with ui.column() as negative_column:
                        negative_column.style('background-color: lightcoral; padding: 10px;')
                        # most true positives among positives
                        # Attributes most commonly and correctly identified by users as robot-like
                        good_markers = sorted(
                            self.callbacks.most_successful_markers(4, 10),
                            key=lambda x: x[1], reverse=True
                        )
                        for i, (each_marker, each_score) in enumerate(good_markers):
                            each_indicator_label = ui.markdown(
                                f"{each_score:.0%} von KI Texten sind ***{each_marker}***"
                            )

                    with ui.column() as positive_column:
                        positive_column.style('background-color: lightgreen; padding: 10px;')
                        # most false positives among negatives
                        # Attributes users most commonly mistake as robot-like in human-written text
                        bad_markers = sorted(
                            self.callbacks.least_successful_markers(4, 10),
                            key=lambda x: x[1], reverse=True
                        )
                        for i, (each_marker, each_score) in enumerate(bad_markers):
                            each_indicator_label = ui.markdown(
                                f"{each_score:.0%} von echten Texten sind **nicht** ***{each_marker}***"
                            )

