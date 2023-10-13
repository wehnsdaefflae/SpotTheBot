# coding=utf-8
import hashlib
from typing import Callable

from nicegui import ui, app
from nicegui.elements.label import Label

from src.gui.page_content_about import about_content
from src.dataobjects import SecretName, User
from src.gui.frame import create_footer
from src.gui.page_content_friends import friends_content
from src.gui.page_content_game import game_content
from src.gui.page_content_results import results_content
from src.gui.tools import download_vcard
from src.tools.names import generate_name, generate_superhero_name


class View:
    def __init__(self):
        self.get_user = None
        self.create_user = None

        self.setup_routes()

    def set_get_user(self, callback: Callable[[str], User]) -> None:
        self.get_user = callback

    def set_create_user(self, callback: Callable[[str, str], None]) -> None:
        self.create_user = callback

    async def logout(self, name: str) -> None:
        with ui.dialog() as dialog, ui.card():
            ui.label(f"Hey {name}! Are you sure you want to log out?")
            with ui.row() as button_row:
                ui.button("yes", on_click=lambda: dialog.submit("yes"))
                ui.button("no", on_click=lambda: dialog.submit("no"))

        result = await dialog
        if result == "yes":
            app.storage.user.pop("user_name", None)
            app.storage.user.pop("secure", None)
            ui.open("/")

    def invite(self, public_name: str, secret_name: str) -> None:
        with ui.dialog() as dialog, ui.card():
            ui.label(f"Send them this link to add them to your friends:")
            ui.label(f"spotthebot.app/invite?=3489fn5f247g25g")

        dialog.open()

    def randomize_name(self, label_name: Label, secret_name: SecretName, checkbox: ui.checkbox) -> None:
        label_name.text = generate_superhero_name()
        secret_name.name = generate_name()
        checkbox.value = True

    def start_game(self, user_name: str, secret_name: SecretName, secure_identity: bool) -> None:
        if secure_identity:
            source_file_path, target_file_name = download_vcard(user_name, secret_name.name)
            app.storage.user["identity_file"] = source_file_path

            ui.download(source_file_path, filename=target_file_name)

            # os.remove(file_name)

        app.storage.user["user_name"] = user_name
        app.storage.user.pop("secure")
        ui.open("/game")

    async def log_in(self, secret_identity: str, secret_name: SecretName, label_public_name: ui.label, secure_identity: bool) -> None:
        if len(secret_identity) < 1:
            return

        name_hash = hashlib.sha256(secret_identity.encode()).hexdigest()
        try:
            # retrieve according public name and assign to
            user = self.get_user(name_hash)
            self.start_game(user.public_name, secret_name, secure_identity)

        except KeyError:
            with ui.dialog() as dialog, ui.card():
                ui.label("Sorry, I don't know your secret identity. Did you mistype?")

            await dialog
            app.storage.user.pop("user_name", None)
            app.storage.user.pop("secure", None)

            ui.open("/")

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

                user_name = app.storage.user.get("user_name", generate_superhero_name())
                # get_random_name

                secret_name = SecretName()

                button_start = ui.button(
                    "SPOT THE BOT", on_click=lambda: self.start_game(label_name.text, secret_name, checkbox.value)
                )
                checkbox = ui.checkbox("Secure secret identity as phone contact.", value=app.storage.user.get("secure", True))

                label_welcome = ui.label(f"as the super hero")

                label_name = ui.label(user_name)
                label_name.classes("cursor-pointer")
                label_name.on("click", lambda: self.randomize_name(label_name, secret_name, checkbox))

                ui.label(f"or")

                invite_button = ui.button("Invite a friend", on_click=lambda: self.invite(user_name, secret_name.name))

                ui.label(f"or")

                enter_text = ui.input("take on your secret identity")
                enter_text.on("change", lambda: self.log_in(enter_text.value, secret_name, label_name, checkbox.value))

                ui.label(f"or")

                label_logout = ui.label("[logout]")
                label_logout.classes("cursor-pointer")
                label_logout.on("click", lambda: self.logout(label_name.text))

                # enter secret identity

                create_footer()
