# coding=utf-8
import hashlib
import random

from nicegui import ui, Client

from src.dataobjects import ViewCallbacks, Face
from src.gui.elements.content_class import ContentPage
from src.gui.elements.dialogs import info_dialog, input_dialog, option_dialog
from src.gui.elements.face import show_face
from src.gui.tools import download_vcard, get_from_local_storage, set_in_local_storage, remove_from_local_storage
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


async def login() -> None:
    secret_name = await input_dialog("Enter your secret name.")
    name_hash = hashlib.sha256(secret_name.encode()).hexdigest()
    await set_in_local_storage("name_hash", name_hash)
    ui.open("/")


class StartContent(ContentPage):
    def __init__(self, client: Client, callbacks: ViewCallbacks) -> None:
        super().__init__(client, callbacks)
        self.face = None
        self.user = None
        self.invited_by_id = None
        ui.add_head_html('<link rel="stylesheet" type="text/css" href="assets/styles/start.css">')
        #ui.add_body_html(
        #    """
        #    <style>
        #        *, ::before, ::after {
        #          all: initial !important;
        #        }
        #    </style>
        #    """
        #)

    async def _set_user(self, name_hash: str | None) -> None:
        if name_hash is None:
            self.user = None
            self.face = Face()
            return

        user = self.callbacks.get_user(name_hash)
        if user is not None:
            self.user = user
            self.face = user.face
            return

        msg = "Sorry, there's no user with that identity. Did you mistype?"
        await remove_from_local_storage("name_hash")
        logger.error(msg)
        await info_dialog(msg)
        self.user = None
        self.face = Face()

    async def _start_game(self) -> None:
        if self.user is None:
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
            name_hash = await get_from_local_storage("name_hash")
            if name_hash != user.secret_name_hash:
                raise ValueError("Something went wrong with the local storage.")

        ui.open("/game")

    async def _confirm_end_friendship(self, friend_id: int) -> None:
        with ui.dialog() as dialog, ui.card():
            ui.label("Are you sure you want to end this friendship?")
            ui.button("Yes", on_click=lambda: dialog.submit("yes"))
            ui.button("No", on_click=lambda: dialog.submit("no"))

        result = await dialog
        if result == "yes":
            logger.info("Ending friendship")
            self.callbacks.remove_friendship(self.user.db_id, friend_id)
            ui.open("/")
        else:
            logger.info("Not ending friendship")

    async def _invite(self) -> None:
        name_hash = await get_from_local_storage("name_hash")
        if name_hash is None:
            link = "spotthebot.app"
        else:
            user = self.callbacks.get_user(name_hash)
            invitation_hash = self.callbacks.create_invitation(user)
            link = f"spotthebot.app/invitation?value={invitation_hash}"

        with ui.dialog() as dialog, ui.card():
            ui.label(f"Give them this link:")
            # use name hash and friend name to create a link
            ui.label(link)

        dialog.open()

    async def create_content(self) -> None:
        logger.info("Start page")

        await self.client.connected()

        name_hash = await get_from_local_storage("name_hash")
        await self._set_user(name_hash)

        with ui.element("div") as container:
            container.classes("container")

            # --- title start
            with ui.element("div") as outer:
                outer.classes("game-title pixel-corners-soft")

                with ui.element("header") as header:
                    title = ui.label("Spot The Bot")

                with ui.element("div") as game_subtitle:
                    game_subtitle.classes("game-subtitle")
                    subtitle = ui.label("Mensch oder Maschine?")

            # --- title end

            # --- main start
            with ui.element("div") as line:
                line.classes("dashed-line")

            name = "Detektiv" if self.user is None else self.user.public_name
            with ui.markdown(f"Willkommen, ***{name}!***") as subheader:
                subheader.classes("welcome")

            with ui.element("div") as info:
                info.classes("info")

                ui.label("Willkommen bei \"Spot The Bot!\"")
                ui.label(
                    "Hier wirst Du zum Detektiv, indem Du herausfindest, ob Texte von einem Bot oder einem Menschen "
                    "kommen. Kannst Du den Unterschied zu erkennen oder wirst Du von Bots an der Nase rumgeführt? "
                    "Schau Dir an, was Texte von echten Menschen von mashinengeschriebenen utnerscheidet damit Du "
                    "weißt, worauf Du achten musst."
                )
                ui.label("Los geht's, zeig den Bots, wer der Boss ist!")
                ui.label("Viel Spaß beim Rätseln!")

            with ui.element("div") as side_left:
                side_left.classes("left-info pixel-corners-hard")

                with ui.label("Texte von Bots sind") as left_header:
                    left_header.classes("flanks-title")

                good_markers = sorted(
                    self.callbacks.most_successful_markers(4, 10),
                    key=lambda x: x[1], reverse=True
                )

                with ui.element("div") as markers:
                    markers.classes("markers")
                    for i, (each_marker, each_score) in enumerate(good_markers):
                        with ui.label(each_marker) as each_indicator_label:
                            each_indicator_label.classes("indicator")

            with ui.element("div") as avatar:
                avatar.classes("avatar-and-controls pixel-corners-hard--wrapper")
                with ui.image(f"assets/images/portraits/{self.face.source_id}-2.png") as image:
                    image.classes("avatar-image")
                with ui.button("Login") as button:
                    button.classes("login eightbit-btn eightbit-btn--proceed")

            with ui.element("div") as side_right:
                side_right.classes("right-info pixel-corners-hard")

                with ui.markdown("Echte Texte sind <ins>nicht</ins>") as left_header:
                    left_header.classes("flanks-title")

                good_markers = sorted(
                    self.callbacks.least_successful_markers(4, 10),
                    key=lambda x: x[1], reverse=True
                )
                with ui.element("div") as markers:
                    markers.classes("markers")
                    for i, (each_marker, each_score) in enumerate(good_markers):
                        with ui.label(each_marker) as each_indicator_label:
                            each_indicator_label.classes("indicator")

            with ui.button("Spiel starten") as start_button:
                start_button.classes("start eightbit-btn")
            # --- main end

            # --- friends start
            with ui.element("div") as line:
                line.classes("dashed-line")

            with ui.element("div") as subheader:
                subheader.classes("welcome")
                ui.label("KollegInnen")

            with ui.element("section") as friends_gallery:
                friends_gallery.classes("friends-gallery")

                if self.user is not None:
                    friends = self.callbacks.get_friends(self.user.db_id)
                    for each_friend in friends:
                        with ui.element("div") as friend:
                            friend.classes("friend pixel-corners-hard--wrapper")
                            with ui.image(f"assets/images/portraits/{each_friend.face.source_id}-2.png") as image:
                                image.classes("friend-avatar")
                            with ui.label(each_friend.name) as name:
                                name.classes("friend-name")
                            with ui.label(f"Wins: {10}") as friend_stats:
                                friend_stats.classes("friend-stats")

                with ui.element("div") as friend:
                    friend.classes("friend add-friend pixel-corners-hard--wrapper")
                    with ui.image("assets/images/portraits/add_friend.png") as image:
                        image.classes("friend-avatar")
                    with ui.label("Freund einladen") as name:
                        name.classes("friend-name")
                    with ui.label("(hier klicken)") as friend_stats:
                        friend_stats.classes("friend-stats")

            with ui.element("div") as line:
                line.classes("dashed-line")

            with ui.label("Footer") as subheader:
                subheader.classes("welcome")



    async def _create_content(self) -> None:
        logger.info("Start page")

        await self.client.connected()

        name_hash = await get_from_local_storage("name_hash")
        await self._set_user(name_hash)

        with ui.grid(columns=3, rows=2) as grid_title:
            grid_title.style("margin: 0; padding: 0; gap: 0;")
            grid_title.classes("w-full h-32")

            title_bot = ui.image("assets/images/elements/title_bot.png")
            title = ui.image("assets/images/elements/title.png")
            title_human = ui.image("assets/images/elements/title_human.png")

            if name_hash is None:
                login_button = ui.button("Log in", on_click=login)

            else:
                label_logout = ui.button("Log out", on_click=logout)


        with ui.column() as top_column:
            top_column.classes("items-center justify-center h-full w-full")

            title_label = ui.label("Spot the Bot")
            title_label.classes("text-h2")

            if self.user is None:
                if self.invited_by_id is None:
                    ui.label(f"Oh... ein neues Gesicht.")
                else:
                    invitee = self.callbacks.get_user_by_id(self.invited_by_id)
                    ui.label(f"So, Du kommst also von {invitee.public_name}.")
            else:
                if self.invited_by_id is None:
                    ui.label(f"Willkommen zurück, {self.user.public_name}!")
                else:
                    invitee = self.callbacks.get_user_by_id(self.invited_by_id)

                    option = await option_dialog(
                        f"Willst Du mit {invitee.public_name} befreundet sein?",
                        ["ja", "nein"]
                    )
                    if option == "ja":
                        self.callbacks.make_friends(
                            self.invited_by_id,
                            self.user.db_id
                        )

            with ui.row() as row:
                label_results = ui.label("check out results")
                label_results.classes("cursor-pointer")
                label_results.on("click", lambda: ui.open("/results"))

                label_about = ui.label("about")
                label_about.classes("cursor-pointer")
                label_about.on("click", lambda: ui.open("/about"))


            with ui.column() as main_column:
                main_column.classes("items-center justify-center")
                # main_row.classes("items-center")

                with ui.column() as column:
                    column.classes("items-center justify-center")

                    face_element = show_face(self.face)
                    face_element.classes("w-64 justify-center")
                    # face_element.classes("w-64 justify-center")

                with ui.column() as mid_column:
                    mid_column.classes("items-center justify-center")
                    button_start = ui.button("Start!", on_click=self._start_game)

        with ui.column() as bottom_column:
            bottom_column.classes("items-center justify-center h-full w-full")
            hints = ui.markdown("Hinweise:")
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

        user = self.callbacks.get_user(name_hash)
        if user is None:
            pass

        else:
            with ui.column() as friends_column:
                hints = ui.markdown("KollegInnen")
                hints.classes("text-h3")

                friends = self.callbacks.get_friends(user.db_id)
                for each_friend in friends:
                    with ui.row():
                        friend_face = show_face(each_friend.face)
                        ui.label(each_friend.name)
                        ui.button(
                            "Remove",
                            on_click=lambda friend_id=each_friend.db_id: self._confirm_end_friendship(friend_id)
                        )

        invite_button = ui.button("Invite a friend", on_click=self._invite)


