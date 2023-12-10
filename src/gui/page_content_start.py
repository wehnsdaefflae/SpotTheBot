# coding=utf-8
import hashlib
import os
import tempfile
import uuid

import qrcode

from nicegui import ui, Client

from src.dataobjects import ViewCallbacks, Face
from src.gui.elements.content_class import ContentPage
from src.gui.elements.dialogs import info_dialog, input_dialog, option_dialog
from src.gui.elements.face import show_face
from src.gui.tools import get_from_local_storage, set_in_local_storage, remove_from_local_storage, serve_id_file, \
    make_xml
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
        ui.add_head_html("<link rel=\"stylesheet\" type=\"text/css\" href=\"assets/styles/start.css\">")

    def _init_javascript(self) -> None:
        init_js = (
            "window.spotTheBot = {",
            "    openDialog: function(event) {",
            "        document.getElementById('fileid').click();",
            "    },",
            "    logout: function(event) {",
            "        localStorage.removeItem('name_hash');",
            "        window.location.reload();",
            "    },",
            "    onLoaded: function(event) {",
            "        console.log('loaded');",
            "        let contents = event.target.result;",
            "        let lines = contents.split('\\n');",
            "        if (lines.length >= 2) {",
            "            let secondLine = lines[1].trim();"
            "            spotTheBot.hashAndStore(secondLine);",
            "            window.location.reload();",
            "        } else {",
            "            console.log(\"The file does not have a second line.\");",
            "        }",
            "    },",
            "    onUpload: function(event) {",
            "       console.log('uploading');",
            "       let file = document.getElementById('fileid').files[0];",
            "       let reader = new FileReader();",
            "       reader.onload = spotTheBot.onLoaded;",
            "       reader.readAsText(file);",
            "    },",
            "    hashAndStore: async function(data) {",
            "        const encoder = new TextEncoder();",
            "        const dataEncoded = encoder.encode(data);",
            "        const hashBuffer = await crypto.subtle.digest('SHA-256', dataEncoded);",
            "        const hashArray = Array.from(new Uint8Array(hashBuffer));",
            "        const hashHex = hashArray.map(b => b.toString(16).padStart(2, '0')).join('');",
            "        localStorage.setItem('name_hash', hashHex);",
            "        console.log(`Hashed second line: ${hashHex}`);",
            "    }",
            "};",
            "document.getElementById('fileid').addEventListener('change', spotTheBot.onUpload, false);",
            "let button = document.getElementById('buttonid');"
        )

        if self.user is None:
            init_js += (
                "button.addEventListener('click', spotTheBot.openDialog);",
                "button.value = 'Log in';",

            )
        else:
            init_js += (
                "button.addEventListener('click', spotTheBot.logout);",
                "button.value = 'Log out';",
            )

        _ = ui.run_javascript("\n".join(init_js))

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
            public_name = await input_dialog("Gib Deinen Namen ein.")

            secret_name = uuid.uuid4().hex

            invited_by_user_id = -1
            user = self.callbacks.create_user(secret_name, self.face, public_name, invited_by_user_id)

            if self.invited_by_id is not None:
                self.callbacks.make_friends(user.db_id, self.invited_by_id)

            source_path, target_path = serve_id_file(secret_name)

            await info_dialog(
                "Merk Dir, wo Du die Datei gespeichert hast. Du brauchst sie, um Dich wieder einzuloggen. "
                "Beende das Spiel immer mit dem \"quit\" Button, um Strafpunkte zu vermeiden."
            )

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

        qr = qrcode.make(link)
        ram_disk_path = "/dev/shm/"

        with tempfile.NamedTemporaryFile(dir=ram_disk_path, mode="bw", suffix=".png", delete=False) as file:
            qr.save(file)

        with ui.dialog() as dialog, ui.card():
            ui.image(file.name)
            ui.label(f"Teile diesen Link:")
            ui.label(link)

        dialog.open()

        # todo: delete qr image file

    async def create_content(self) -> None:
        logger.info("Start page")
        await self.client.connected()

        name_hash = await get_from_local_storage("name_hash")
        await self._set_user(name_hash)

        with ui.element("div") as container:
            container.classes("container")

            self._render_title()
            await self._render_welcome()
            self._render_main()

            with ui.button("Spiel starten", on_click=self._start_game) as start_button:
                start_button.classes("start eightbit-btn")

            if self.user is not None:
                self._render_friends_gallery()

            self._render_footer()

            self._init_javascript()

    async def _render_welcome(self) -> None:
        #with ui.element("div") as line:
        #    line.classes("dashed-line")

        if self.user is None:
            if self.invited_by_id is None:
                welcome_message = ui.label(f"Oh... ein neues Gesicht.")
            else:
                invitee = self.callbacks.get_user_by_id(self.invited_by_id)
                welcome_message = ui.label(f"So, Du kommst also von {invitee.public_name}.")
        else:
            welcome_message = ui.label(f"Willkommen zurück, {self.user.public_name}!")
            if self.invited_by_id is not None:
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

        welcome_message.classes("welcome")

        with ui.expansion("Was ist \"Spot The Bot\"?", value=self.user is None) as info:
            info.classes("info")

            ui.label(
                "Hier wirst Du zum Detektiv, indem Du herausfindest, ob Texte von einem Bot oder einem Menschen "
                "kommen. Kannst Du den Unterschied zu erkennen oder wirst Du von Bots an der Nase rumgeführt? "
                "Schau Dir an, was Texte von echten Menschen von maschinengeschriebenen unterscheidet damit Du "
                "weißt, worauf Du achten musst."
            )
            ui.label("Los geht's, zeig den Bots, wer der Boss ist!")
            ui.label("Viel Spaß beim Rätseln!")

    def _render_main(self) -> None:
        with ui.element("div") as side_left:
            side_left.classes("left-info pixel-corners-hard")

            with ui.label("Texte von Bots sind") as left_header:
                left_header.classes("flanks-title")

            good_markers = sorted(
                self.callbacks.most_successful_markers(7, 10),
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

            with ui.html("<input id='fileid' type='file' hidden/>") as file_input:
                pass

            input_html = make_xml(
                "input", void_element=True,
                id="buttonid", type="button", value="",
                class_="login-button eightbit-btn--proceed pixel-corners-hard--wrapper"
            )
            with ui.html(input_html) as login_button:
                pass

        with ui.element("div") as side_right:
            side_right.classes("right-info pixel-corners-hard")

            with ui.markdown("Echte Texte sind <ins>nicht</ins>") as left_header:
                left_header.classes("flanks-title")

            good_markers = sorted(
                self.callbacks.least_successful_markers(7, 10),
                key=lambda x: x[1], reverse=True
            )
            with ui.element("div") as markers:
                markers.classes("markers")
                for i, (each_marker, each_score) in enumerate(good_markers):
                    with ui.label(each_marker) as each_indicator_label:
                        each_indicator_label.classes("indicator")

    def _render_title(self) -> None:
        with ui.element("div") as outer:
            outer.classes("game-title pixel-corners-soft")

            with ui.element("header") as header:
                title = ui.label("Spot The Bot")

            with ui.element("div") as game_subtitle:
                game_subtitle.classes("game-subtitle")
                subtitle = ui.label("Mensch oder Maschine?")

    def _render_footer(self):
        with ui.element("div") as line:
            line.classes("dashed-line")

        with ui.label("Footer") as subheader:
            subheader.classes("welcome")

    def _render_friends_gallery(self) -> None:
        with ui.element("div") as line:
            line.classes("dashed-line")

        # --- friends start
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

            # friend.on("click", lambda e: ui.notify("Not implemented yet"))
            friend.on("click", self._invite)


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
