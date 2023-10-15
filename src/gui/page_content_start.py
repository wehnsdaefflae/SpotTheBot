import hashlib
import random
from typing import Callable

from nicegui import ui, app

from src.dataobjects import User, ViewCallbacks, ViewStorage
from src.gui.frame import create_footer
from src.gui.tools import download_vcard
from src.tools.names import generate_name


def retrieve_user_and_secret(get_user: Callable[[str], User]) -> tuple[User, str]:
    name_hash = app.storage.user.get("name_hash", None)
    if name_hash is None:
        ui.tooltip("No user hash stored.")

    else:
        try:
            user = get_user(name_hash)
            ui.tooltip(f"Retrieving user with hash {name_hash}.")
            return user, ""

        except KeyError:
            ui.tooltip(f"No user with hash {name_hash} found. Removing hash...")
            app.storage.user.pop("name_hash", None)

    name_seed = tuple(random.random() for _ in range(7))
    secret_name = generate_name(name_seed)
    name_hash = hashlib.sha256(secret_name.encode()).hexdigest()

    return User(name_hash), secret_name


async def invite(name_hash: str) -> None:
    with ui.dialog() as dialog, ui.card():
        ui.label(f"What's their name?")
        user_name = ui.input("name of friend")
        user_name.on("change", lambda: dialog.submit(user_name.value))

    friend_name = await dialog

    if friend_name is None or len(friend_name) < 1:
        return

    with ui.dialog() as dialog, ui.card():
        ui.label(f"Give this link to {friend_name} to add them to your friends:")
        # use name hash and friend name to create a link
        ui.label(f"spotthebot.app/invite?=3489fn5f247g25g")

    dialog.open()


async def start_game(create_user: Callable[[User], str], view_storage: ViewStorage, user: User, secret_name: str) -> None:
    if len(secret_name) >= 1:
        assert user.db_id < 0
        with ui.dialog().props("persistent") as dialog, ui.card():
            ui.label("Welcome! Please keep the following file safe!")
            ui.button("ok", on_click=lambda: dialog.submit("ok"))

        await dialog
        user_key = create_user(user)
        view_storage.user = user
        source_file_path, target_file_name = download_vcard(secret_name)
        app.storage.user["identity_file"] = source_file_path
        ui.download(source_file_path, filename=target_file_name)
        app.storage.user["name_hash"] = user.secret_name_hash

    ui.open("/game")


async def log_in(get_user: Callable[[str], User], create_user: Callable[[User], str], secret_identity: str) -> None:
    if len(secret_identity) < 1:
        return

    name_hash = hashlib.sha256(secret_identity.encode()).hexdigest()
    try:
        # retrieve according public name and assign to
        user = get_user(name_hash)
        await start_game(create_user, user, secret_identity)

    except KeyError:
        with ui.dialog() as dialog, ui.card():
            ui.label("Sorry, I don't know your secret identity. Did you mistype?")

        await dialog
        app.storage.user.pop("name_hash", None)

        ui.open("/")


def start_content(view_storage: ViewStorage, callbacks: ViewCallbacks) -> None:
    from loguru import logger
    logger.info("Start page")

    with ui.column() as column:
        title_label = ui.label("Look out for robots!")
        title_label.classes("text-h4 font-bold text-grey-8")

        for i in range(4):
            each_indicator_label = ui.label(f"[indicator {i + 1}] [accuracy]")

        user, secret_name = retrieve_user_and_secret(callbacks.get_user)

        # get_random_name
        ui.label(f"[face]")

        ui.label("this isn't you?")
        enter_text = ui.input("take on your secret identity")
        enter_text.on(
            "change",
            lambda: log_in(callbacks.get_user, callbacks.create_user, enter_text.value)
        )

        button_start = ui.button(
            "SPOT THE BOT",
            on_click=lambda: start_game(callbacks.create_user, view_storage, user, secret_name)
        )

        ui.label(f"or")

        invite_button = ui.button(
            "Invite a friend",
            on_click=lambda: invite(user.secret_name_hash)
        )

        create_footer(view_storage)
