# coding=utf-8
import hashlib
import random
from typing import Callable

from nicegui import ui, app

from src.dataobjects import User, ViewCallbacks, ViewStorage
from src.gui.frame import create_footer
from src.gui.tools import download_vcard
from src.tools.names import generate_name
from loguru import logger


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
        # return app url
        pass

    with ui.dialog() as dialog, ui.card():
        ui.label(f"Give this link to {friend_name} to add them to your friends:")
        # use name hash and friend name to create a link
        ui.label(f"spotthebot.app/invite?=3489fn5f247g25g")

    dialog.open()


async def start_game(create_user: Callable[[User], str], get_user: Callable[[str], User], view_storage: ViewStorage, identity_input: ui.input) -> None:
    secret_identity = identity_input.value

    if len(secret_identity) >= 1:
        user_hash = hashlib.sha256(secret_identity.encode()).hexdigest()

    else:
        user_hash = app.storage.user.get("name_hash", None)

    if user_hash is None:
        secret_identity = generate_name(tuple(random.random() for _ in range(7)))
        user_hash = hashlib.sha256(secret_identity.encode()).hexdigest()
        user = User(secret_name_hash=user_hash)
        create_user(user)

        with ui.dialog().props("persistent") as dialog, ui.card():
            ui.label("Welcome! Please keep the following file safe!")
            ui.button("ok", on_click=lambda: dialog.submit("ok"))

        await dialog

        source_file_path, target_file_name = download_vcard(secret_identity)
        app.storage.user["identity_file"] = source_file_path
        ui.download(source_file_path, filename=target_file_name)

    else:
        try:
            user = get_user(user_hash)
            view_storage.users[user_hash] = user

        except KeyError:
            app.storage.user.pop("name_hash", None)
            identity_input.value = ""
            with ui.dialog().props("persistent") as dialog, ui.card():
                ui.label("Sorry, there's no user with that identity. Did you mistype?")

            await dialog
            return

    app.storage.user["name_hash"] = user_hash

    ui.open("/game")


def start_content(view_storage: ViewStorage, callbacks: ViewCallbacks) -> None:
    logger.info("Start page")

    with ui.column() as column:
        title_label = ui.label("Look out for robots!")
        title_label.classes("text-h4 font-bold text-grey-8")

        for i in range(4):
            each_indicator_label = ui.label(f"[indicator {i + 1}] [accuracy]")

        # get_random_name
        ui.label(f"[face]")

        ui.label("this isn't you?")
        enter_text = ui.input("take on your secret identity")
        enter_text.on(
            "change",
            lambda: start_game(callbacks.create_user, callbacks.get_user, view_storage, enter_text)
        )

        button_start = ui.button(
            "SPOT THE BOT",
            on_click=lambda: start_game(callbacks.create_user, callbacks.get_user, view_storage, enter_text)
        )

        ui.label(f"or")

        invite_button = ui.button(
            "Invite a friend",
            on_click=invite
        )

        create_footer(view_storage)
