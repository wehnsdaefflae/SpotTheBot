# coding=utf-8
import hashlib
import random
from typing import Callable

from nicegui import ui, app
from nicegui.elements.label import Label

from src.gui.page_content_about import about_content
from src.dataobjects import SecretName, User, State
from src.gui.frame import create_footer
from src.gui.page_content_friends import friends_content
from src.gui.page_content_game import game_content
from src.gui.page_content_results import results_content
from src.gui.tools import download_vcard
from src.tools.names import generate_name, generate_superhero_name, generate_face


class View:
    def __init__(self):
        self.get_user = None
        self.create_user = None

        self.setup_routes()

    def set_get_user(self, callback: Callable[[str], User]) -> None:
        self.get_user = callback

    def set_create_user(self, callback: Callable[[User], str]) -> None:
        self.create_user = callback

    async def logout(self) -> None:
        with ui.dialog() as dialog, ui.card():
            ui.label("Are you sure you want to log out?")
            with ui.row() as button_row:
                ui.button("yes", on_click=lambda: dialog.submit("yes"))
                ui.button("no", on_click=lambda: dialog.submit("no"))

        result = await dialog
        if result == "yes":
            app.storage.user.pop("name_hash", None)
            app.storage.user.pop("identity_file", None)

            ui.open("/")

    async def invite(self, name_hash: str) -> None:
        with ui.dialog() as dialog, ui.card():
            ui.label(f"What's their name?")
            user_name = ui.input("name of friend")
            user_name.on("change", lambda: dialog.submit(user_name.value))

        friend_name = await dialog

        with ui.dialog() as dialog, ui.card():
            ui.label(f"Give this link to {friend_name} to add them to your friends:")
            # use name hash and friend name to create a link
            ui.label(f"spotthebot.app/invite?=3489fn5f247g25g")

        dialog.open()

    def randomize_name(self, label_name: Label, secret_name: SecretName, checkbox: ui.checkbox) -> None:
        label_name.text = generate_superhero_name()
        secret_name.name = generate_name()
        checkbox.value = True

    def start_game(self, user: User, secret_name: str) -> None:
        if len(secret_name) < 1:
            assert user.db_id < 0
            user_key = self.create_user(user)
            source_file_path, target_file_name = download_vcard(secret_name)
            app.storage.user["identity_file"] = source_file_path
            ui.download(source_file_path, filename=target_file_name)

        app.storage.user["name_hash"] = user.secret_name_hash
        ui.open("/game")

    async def log_in(self, secret_identity: str) -> None:
        if len(secret_identity) < 1:
            return

        name_hash = hashlib.sha256(secret_identity.encode()).hexdigest()
        try:
            # retrieve according public name and assign to
            user = self.get_user(name_hash)
            self.start_game(user, secret_identity)

        except KeyError:
            with ui.dialog() as dialog, ui.card():
                ui.label("Sorry, I don't know your secret identity. Did you mistype?")

            await dialog
            app.storage.user.pop("name_hash", None)

            ui.open("/")

    def retrieve_user_and_secret(self) -> tuple[User, str]:
        name_hash = app.storage.user.get("name_hash", None)
        if name_hash is not None:
            try:
                user = self.get_user(name_hash)
                return user, ""
            except KeyError:
                ui.tooltip(f"No User with name hash {name_hash} found.")

        name_seed = tuple(random.random() for _ in range(7))
        secret_name = generate_name(name_seed)
        name_hash = hashlib.sha256(secret_name.encode()).hexdigest()
        app.storage.user["name_hash"] = name_hash

        face_seed = tuple(random.random() for _ in range(7))
        face = generate_face(face_seed)

        return User(name_hash, face, State(), set()), secret_name

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
            game_content()

        @ui.page("/")
        def index_page() -> None:
            with ui.column() as column:
                title_label = ui.label("Look out for robots!")
                title_label.classes("text-h4 font-bold text-grey-8")

                for i in range(4):
                    each_indicator_label = ui.label(f"[indicator {i + 1}] [accuracy]")

                user, secret_name = self.retrieve_user_and_secret()

                # get_random_name
                button_start = ui.button("SPOT THE BOT", on_click=lambda: self.start_game(user, secret_name))

                invite_button = ui.button("Invite a friend", on_click=lambda: self.invite(user.secret_name_hash))

                ui.label(f"or")

                ui.label(f"[face]")

                ui.label("this isnt you?")
                enter_text = ui.input("take on your secret identity")
                enter_text.on("change", lambda: self.log_in(enter_text.value))

                ui.label(f"or")

                label_logout = ui.label("[logout]")
                label_logout.classes("cursor-pointer")
                label_logout.on("click", self.logout)

                # enter secret identity

                create_footer()
