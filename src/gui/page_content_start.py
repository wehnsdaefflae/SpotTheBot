import uuid
from urllib.parse import urlparse

from loguru import logger
from nicegui import Client, ui

from src.dataobjects import ViewCallbacks, User, Face
from src.gui.elements.content_class import ContentPage
from src.gui.elements.dialogs import info_dialog, option_dialog, input_dialog
from src.gui.tools import get_from_local_storage, remove_from_local_storage, serve_id_file, set_in_local_storage


class StartContent(ContentPage):
    @staticmethod
    def _create_stats(header_text: str, tooltip_text: str, tags: list[tuple[str, float]]) -> None:
        with ui.element() as container:
            with ui.markdown(f"**{header_text}** ⓘ") as header:
                header.classes("text-lg mb-2 text-center ")

            with ui.tooltip() as tooltip:
                with ui.html(tooltip_text) as tooltip_text:
                    tooltip_text.classes("text-sm text-justify w-64 ")

        with ui.element("ol") as box:
            box.classes(
                "flex flex-grow flex-col items-center "
                "list-decimal list-inside bg-red-200 rounded p-2 "
            )
            for each_marker, each_score in tags:
                with ui.markdown(f"*{each_marker}*") as each_tag:
                    each_tag.classes("text-center w-full ")

    def __init__(self, client: Client, callbacks: ViewCallbacks) -> None:
        super().__init__(client, callbacks)
        self._user: User | None = None
        self._face: Face | None = None
        self._invitee_id: int = -1
        self._domain = "https://spotthebot.app"

        self._header_classes = "text-2xl font-semibold text-center py-2 "

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
            "            let secondLine = lines[1].trim();",
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
            "    },",
            "    shareInvitation: function(event) {",
            "        if (navigator.share) {",
            "            console.log('share supported');",
            "            navigator.share({",
            "                title: 'Spot The Bot!',",
            "                text: 'Mensch oder Maschine?',",
            f"                url: '{self._domain}'",
            "            }).then(() => {",
            "                console.log('Thanks for sharing!');",
            "            }).catch((error) => {",
            "                console.log('Error sharing:', error);",
            "            });",
            "        } else {",
            "            console.log('share not supported');",
            "        }",
            "    }",
            "};",
            "document.getElementById('fileid').addEventListener('change', spotTheBot.onUpload, false);",
            "let button = document.getElementById('buttonid');",
            # "if (localStorage.getItem('name_hash') !== null) {",
            # "    let inviteButton = document.getElementById('inviteButton');",
            # "    inviteButton.addEventListener('click', spotTheBot.shareInvitation);",
            # "}"
        )

        if self._user is None:
            init_js += (
                "button.addEventListener('click', spotTheBot.openDialog);",
            )
        else:
            init_js += (
                "button.addEventListener('click', spotTheBot.logout);",
            )

        _ = ui.run_javascript("\n".join(init_js))

    async def _set_domain(self) -> None:
        js_url = await ui.run_javascript('window.location.href', timeout=3., check_interval=.1)
        parsed_url = urlparse(js_url)
        self._domain = f"{parsed_url.scheme}://{parsed_url.netloc}/"

    async def _set_user(self, name_hash: str | None) -> None:
        if name_hash is None:
            logger.info("No user name hash in local storage.")
            self._user = None
            self._face = Face()
            return

        self._user = self.callbacks.get_user(name_hash)
        if self._user is None:
            remove_from_local_storage("name_hash")
            logger.error("No user found for given name hash.")
            await info_dialog("Der User wurde in der Datenbank nicht gefunden. Bitte erstelle einen neuen User.")
            self._face = Face()
            return

        logger.info(f"User found: {self._user.public_name}")
        self._face = self._user.face

    async def _start_game(self) -> None:
        if self._user is None:
            public_name = await input_dialog(
                "Hallo! Du scheinst neu zu sein. "
                "Bitte gib deinen Namen ein, so dass wir einen User für dich anlegen können.")
            secret_name = uuid.uuid4().hex

            self._user = self.callbacks.create_user(secret_name, self._face, public_name, self._invitee_id)

            if self._invitee_id >= 0:
                self.callbacks.make_friends(self._user.db_id, self._invitee_id)

            source_path, target_path = serve_id_file(secret_name)

            set_in_local_storage("identity_file", source_path)
            set_in_local_storage("name_hash", self._user.secret_name_hash)

            await info_dialog(
                f"<h3>Hallo {public_name}!</h3>"
                f"Bitte lies Dir die folgenden Anweisungen sorgfältig durch:"
                f"<ol>"
                f"<li>Sobald du diese Nachricht wegklickst, wird eine Datei `{target_path}` runtergeladen. Merk Dir, "
                f"wo Du sie gespeichert hast! Du brauchst sie, um dich später wieder einzuloggen.</li>"
                f"<li>Markiere Stellen im Text, die dir verdächtig vorkommen. Wenn du nichts markierst, wird der Text "
                f"als \"echt\" gewertet.</li>"
                f"<li>Beende das Spiel immer nur nach einer Antwort mit dem \"Beenden\" Knopf, um Strafpunkte zu "
                f"vermeiden.</li>"
                f"<li>Je schneller Du antwortest, umso mehr Punkte stehen auf dem Spiel. Die Höchstpunktezahl ist durch "
                f"die Textlänge bestimmt. Die geringste Punktezahl ist 5.</li>"
                f"</ol>"
            )

            ui.download(source_path, target_path)

            name_hash = await get_from_local_storage("name_hash")
            if name_hash != self._user.secret_name_hash:
                raise ValueError("Something went wrong with the local storage.")

        ui.open("/game")

    async def _create_title_container(self) -> None:
        with ui.element("div") as title_container:
            title_container.classes("text-center py-4 max-w-xl ")
            with ui.label("Spot The Bot!") as title:
                title.classes("text-4xl font-bold mb-2 w-full ")

            with ui.label("Mensch oder Maschine?") as subtitle:
                subtitle.classes("text-2xl font-semibold mb-2 w-full ")

            with ui.expansion("Was ist Spot The Bot?", value=self._user is None) as info:
                info.classes("w-full bg-[#B0FFE3] rounded ")
                welcome_text = (
                    "<p>"
                    "<strong><i>Spot The Bot</i></strong> ist eine Plattform für Communities, deren Mitglieder "
                    "spielerisch lernen wollen, KI-generierte von menschengeschriebenen Texten zu unterscheiden."
                    "</p>"
                    "<p>"
                    "Es kann an verschiedene Communities angepasst werden, indem es zum Beispiel Kommentare aus dem "
                    "YouTube-Kanal oder Nachrichten aus dem Discord Server der Community als Basisdaten für das Spiel "
                    "nutzt werden."
                    "</p>"
                    "<p>"
                    "<strong><i>Spot The Bot</i></strong> ist ein Open-Source-Projekt, das von der Community für die "
                    "Community entwickelt wird. Wenn Du mitmachen willst, schau auf <ins><a "
                    "href=\"https://github.com/wehnsdaefflae/SpotTheBot\" target=\"_blank\">GitHub</a></ins> vorbei. "
                    "Für Fragen oder Anregungen hast, <ins><a href=\"mailto:wernsdorfer@gmail.com\">schreib mir "
                    "gerne eine E-Mail</a></ins>."
                    "</p>"
                    "<p>"
                    "Das Projekt wurde im Rahmen des <ins><a href=\"https://prototypefund.de/project/botornot/\" "
                    "target=\"_blank\">Prototype Fund</a></ins> gefördert. Vielen Dank dafür!"
                    "</p>"
                )
                with ui.html(welcome_text) as info_text:
                    info_text.classes("text-lg text-gray-700 text-justify mx-auto ")
                    # info_text.on("click", lambda e: info.set_value(not info.value))

    async def _create_welcome_title(self) -> None:
        if self._user is None:
            if self._invitee_id < 0:
                welcome_message = "Oh... ein neues Gesicht."
            else:
                invitee = self.callbacks.get_user_by_id(self._invitee_id)
                welcome_message = f"So, Du kommst also von {invitee.public_name}?"
        else:
            welcome_message = f"Willkommen zurück, {self._user.public_name}!"
            if self._invitee_id >= 0:
                invitee = self.callbacks.get_user_by_id(self._invitee_id)
                option = await option_dialog(
                    f"Willst du mit {invitee.public_name} befreundet sein?",
                    ["ja", "nein"]
                )
                if option == "ja":
                    self.callbacks.make_friends(self._invitee_id, self._user.db_id)

        with ui.label(welcome_message) as welcome_title:
            welcome_title.classes(self._header_classes)

    def _create_central_image(self) -> None:
        state = "2"  # 2 happy, 0 sad, 1 angry

        if self._user is not None:
            positives = self._user.true_positives + self._user.false_negatives
            negatives = self._user.false_positives + self._user.true_negatives
            false_negative_rate = 0. if 0 >= positives else self._user.false_negatives / positives
            false_positive_rate = 0. if 0 >= negatives else self._user.false_positives / negatives

            if false_negative_rate >= .2 and false_negative_rate >= false_positive_rate:
                state = "0"
            elif false_positive_rate >= .2 and false_positive_rate >= false_negative_rate:
                state = "1"

        with ui.image(f"assets/images/portraits/{self._face.source_id}-{state}.png") as image:
            image.classes("w-64 rounded z-0 ").style("image-rendering: pixelated;")

        with ui.button() as login_button:
            login_button.classes("absolute bottom-5 left-1/2 transform -translate-x-1/2 w-32 z-50 ")
            login_button.props("id=\"buttonid\"")
            with ui.html("<input id='fileid' type='file' hidden/>") as file_input:
                pass

            if self._user is None:
                login_button.set_text("Anmelden")
            else:
                login_button.set_text("Abmelden")

    async def _create_central_content(self) -> None:
        with ui.element("div") as container:
            container.classes("flex justify-evenly md:gap-4 md:grid md:grid-cols-3 my-2 ")
            with ui.element("div") as left_stats:
                left_stats.classes("w-2/5 md:w-full md:col-span-1 flex flex-col")
                bot_tags = sorted(
                    self.callbacks.most_successful_markers(7, 10),
                    key=lambda x: x[1], reverse=True
                )
                bot_header = "Texte von Bots sind"
                bot_tooltip = (
                    "Wenn genug gespielt wurde, findest du hier Hinweise, mit denen deine Mitspielerinnen "
                    "erfolgreich Bots erkannt haben."
                )
                StartContent._create_stats(bot_header, bot_tooltip, bot_tags)

            with ui.element("div") as central_image:
                central_image.classes(
                    "flex place-content-center "
                    "md:col-span-1 relative w-full order-first md:order-none mb-4 md:mb-0 ")
                self._create_central_image()

            with ui.element("div") as right_stats:
                right_stats.classes("w-2/5 md:w-full md:col-span-1 flex flex-col")
                human_tags = sorted(
                    self.callbacks.least_successful_markers(7, 10),
                    key=lambda x: x[1], reverse=True
                )
                human_header = "Echte Texte sind <ins>nicht</ins>"
                human_tooltip = (
                    "Wenn genug gespielt wurde, findest du hier Textmerkmale, die für deine Mitspielerinnen am "
                    "stärksten nach einem Bot klingen, obwohl die Texte von Menschen sind."
                )
                StartContent._create_stats(human_header, human_tooltip, human_tags)

    async def _create_main_container(self) -> None:
        await self._create_welcome_title()
        await self._create_central_content()

        with ui.button("Spiel starten", on_click=self._start_game) as button:
            button.classes("w-5/6 m-8 ")

    async def _confirm_end_friendship(self, friend_id: int) -> None:
        with ui.dialog() as dialog, ui.card():
            ui.label("Willst du die Freundschaft wirklich beenden?")
            ui.button("Ja", on_click=lambda: dialog.submit("Ja"))
            ui.button("Nein", on_click=lambda: dialog.submit("Nein"))

        result = await dialog
        if result == "Ja":
            logger.info(f"Ending friendship between {self._user.db_id} and {friend_id}...")
            self.callbacks.remove_friendship(self._user.db_id, friend_id)
            ui.open("/")
        else:
            logger.info("Not ending friendship.")

    async def _invite(self) -> None:
        name_hash = await get_from_local_storage("name_hash")
        if name_hash is None:
            link = self._domain
        else:
            user = self.callbacks.get_user(name_hash)
            invitation_hash = self.callbacks.create_invitation(user)
            link = f"{self._domain}invitation?value={invitation_hash}"

        with ui.dialog() as dialog, ui.card():
            ui.label(f"Teile diesen Link:").classes("text-lg ")
            ui.label(link).classes("text-lg ")

        dialog.open()

    async def _create_friends_container(self) -> None:
        friends = self.callbacks.get_friends(self._user.db_id)

        with ui.element("div") as container:
            container.classes("py-8 ")

            with ui.label("Friends") as header:
                header.classes(self._header_classes)

            # Friends gallery with consistent layout
            with ui.element("div") as gallery:
                gallery.classes("p-4 my-2 bg-indigo-200 rounded grid grid-cols-4 gap-4 justify-items-center")
                for each_friend in friends:
                    with ui.element("div") as friend:
                        friend.classes("w-20 md:w-40 rounded ")

                        state = "2"  # 2 happy, 0 sad, 1 angry
                        if each_friend.anger >= .2 and each_friend.anger >= each_friend.sadness:
                            state = "1"
                        elif each_friend.sadness >= .2 and each_friend.sadness >= each_friend.anger:
                            state = "0"

                        with ui.image(f"assets/images/portraits/{each_friend.face.source_id}-{state}.png") as image:
                            pass

                        with ui.label(each_friend.name) as name:
                            pass

                        with ui.label(f"Wins: {10}") as friend_stats:
                            pass

                        with ui.button(
                                "entfernen", on_click=lambda e: self._confirm_end_friendship(each_friend.db_id)
                        ) as remove:
                            remove.classes("w-20 md:w-40 ")

                with ui.button("FreundIn einladen", on_click=self._invite) as invite_button:
                    invite_button.classes("w-20 md:w-40 ")
                    invite_button.props("id=\"inviteButton\"")

    async def _create_footer_container(self) -> None:
        with ui.element("div") as container:
            container.classes(" ")
            with ui.label("Footer") as header:
                header.classes(self._header_classes)

    async def create_content(self) -> None:
        logger.info("Index page")
        await self.client.connected()
        name_hash = await get_from_local_storage("name_hash")
        await self._set_user(name_hash)

        with ui.element("div") as main_container:
            main_container.classes("grid grid-cols-1 justify-items-center ")
            await self._create_title_container()
            ui.separator()
            await self._create_main_container()
            ui.separator()
            if self._user is not None:
                await self._create_friends_container()
                ui.separator()
            # await self._create_footer_container()

        await self._set_domain()
        self._init_javascript()
