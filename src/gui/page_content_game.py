from __future__ import annotations
import os

from loguru import logger
from nicegui import ui, Client

from src.dataobjects import ViewCallbacks, User, BinaryStats
from src.gui.elements.content_class import ContentPage
from src.gui.elements.dialogs import info_dialog
from src.gui.elements.interactive_text import InteractiveText
from src.gui.tools import get_from_local_storage


class GameContent(ContentPage):
    def __init__(self, client: Client, callbacks: ViewCallbacks) -> None:
        super().__init__(client, callbacks)
        self.binary_stats_session = BinaryStats()

        self.submit_human = "Sieht gut aus, weiter!"
        self.submit_human_color = "bg-green-200 "

        self.submit_bot = "Das ist ein Bot!"
        self.submit_bot_color = "bg-red-200 "

        self.submit_button: ui.button | None = None

        self.min_points = 5
        self.points = self.max_points = -1

        self.interactive_text: InteractiveText | None = None

        self.timer: ui.timer = ui.timer(1, self._decrement_points, active=False)
        self.user: User | None = None

    def _init_javascript(self, button_id: str) -> None:
        init_js = (
            "window.spotTheBot = {",
            "    tag_count: {},",
            f"    submit_button: document.getElementById('{button_id}'),",
            "    increment: function(tag) {",
            f"        console.log(\"incrementing \" + tag + \"...\"); "
            "        this.tag_count[tag] = (this.tag_count[tag] || 0) + 1;",
            "        this.submit_button.children[1].children[0].innerText = '" + self.submit_bot + "';",
            # "        this.submit_button.setAttribute('color', 'positive');",
            "        return this.tag_count[tag];",
            "    },",
            "    decrement: function(tag) {",
            f"        console.log(\"decrementing \" + tag + \"...\"); ",
            "        this.tag_count[tag]--;",
            "        let sum = 0;",
            "        for (let key in this.tag_count) {",
            "            sum += this.tag_count[key];",
            "        }",
            "        if (sum === 0) {",
            f"            this.submit_button.children[1].children[0].innerText = '{self.submit_human}';",
            # "            this.submit_button.setAttribute('color', 'negative');",
            "        }",
            "        return this.tag_count[tag];",
            "    }",
            "};"
        )
        _ = ui.run_javascript("\n".join(init_js))

    def _decrement_points(self) -> None:
        if self.min_points < self.points:
            self.progress_bar.style(
                f"width: {(self.points - 0) / (self.max_points - 0) * 100:.0f}%;")
            self.points -= 1
            self.progress_bar.classes("bg-yellow-500 ")

        else:
            self.progress_bar.classes("bg-red-500 ")

    async def _check_user(self) -> None:
        name_hash = await get_from_local_storage("name_hash")
        if name_hash is None:
            logger.warning("No name hash found, returning to start page.")
            ui.open("/")
            return

        self.user = self.callbacks.get_user(name_hash)

    async def _apply_penalty(self, user: User) -> None:
        penalize = user.penalty
        logger.info(f"This round penalty: {penalize}")

        if penalize:
            false_positives = user.false_positives + 5.
            false_negatives = user.false_negatives + 5.
            self.callbacks.update_user_state(user, 0, false_positives, 0, false_negatives)

            await info_dialog(
                "Du hast das letzte mal abgebrochen. Dafür bekommst du Strafpunkte :( Versuch bitte immer das "
                "Spiel über den \"Beenden\"-Button zu beenden."
            )

        else:
            self.callbacks.set_user_penalty(user, True)
            logger.info("Setting penalty.")

    async def _add_text_element(self) -> None:
        self.interactive_text = InteractiveText(
            lambda: self.callbacks.get_next_snippet(self.user), lambda: self.submit_button
        )
        self.interactive_text.generate_content()

    def _update_text(self) -> None:
        self.interactive_text.update_content()
        self.interactive_text.reset_tagged_word_count()
        # reset button label
        js = (
            "window.spotTheBot.submit_button.children[1].children[0].innerText = '" + self.submit_human + "';"
            # "window.spotTheBot.submit_button.setAttribute('color', 'negative');"
        )
        _ = ui.run_javascript(js)
        snippet = self.interactive_text.snippet
        word_count = len(snippet.text.split())
        self.points = self.max_points = word_count // 4

    def _add_timing(self) -> None:
        self.timer.activate()

        with ui.column() as points_column:
            points_column.classes("flex justify-center w-full ")
            with ui.element("div") as progress_background:
                progress_background.classes("w-full bg-gray-200 rounded-full h-2.5 dark:bg-gray-700 ")
                with ui.element("div") as self.progress_bar:
                    self.progress_bar.classes("bg-green-500 rounded-full h-full ")

            with ui.row() as points:
                points.classes("flex justify-center text-base w-full ")
                point_text = ui.label().bind_text(self, "points")
                self.text_points = ui.label(" Punkte übrig")

    def _add_stats(self) -> None:
        with ui.row() as stats:
            stats.classes("flex gap-1 ")
            ui.label().bind_text_from(self.binary_stats_session, "false_negatives")
            ui.label("/")
            ui.label().bind_text_from(self.binary_stats_session, "actually_positive")
            ui.label("Bots verpasst")

        with ui.row() as stats:
            stats.classes("flex gap-1 ")
            ui.label().bind_text_from(self.binary_stats_session, "false_positives")
            ui.label("/")
            ui.label().bind_text_from(self.binary_stats_session, "actually_negative")
            ui.label("Menschen verwechselt")

    def _add_avatar(self, actually_positive: bool, classified_positive: bool) -> None:
        state = "2"  # 2 happy, 0 sad, 1 angry
        if not actually_positive and classified_positive:
            state = "1"
        elif actually_positive and not classified_positive:
            state = "0"

        emotion = "ᕕ( ᐛ )ᕗ"
        if actually_positive and classified_positive:
            emotion = "Du hast den Bot erkannt! (◕‿◕✿)"
        elif not actually_positive and classified_positive:
            emotion = "Vorsicht! Das war ein Mensch... (╯°□°)╯︵ ┻━┻"
        elif actually_positive and not classified_positive:
            emotion = "Der Bot ist dir entwischt! (◡︵◡)"
        elif not actually_positive and not classified_positive:
            emotion = "Richtig! Das war ein Mensch! ᕕ( ᐛ )ᕗ"

        with ui.label(f"{emotion}") as name:
            name.classes("text-center text-base w-full ")
            pass

        with ui.image(f"assets/images/portraits/{self.user.face.source_id}-{state}.png") as image:
            image.classes("mx-auto w-32 md:w-64 ")
            image.style("image-rendering: pixelated;")

    async def _feedback_dialog(
            self, actually_positive: bool, classified_positive: bool, interactive_text: InteractiveText) -> None:
        base_truth = "BOT" if actually_positive else "HUMAN"
        classification = "BOT" if classified_positive else "HUMAN"

        message = (
            f"{self.user.public_name} classified {base_truth} text "
            f"{interactive_text.snippet.db_id} as {classification} "
            f"with {self.points} points certainty of {self.max_points} total."
        )

        with ui.dialog().props("persistent") as dialog, ui.card() as card:
            if actually_positive == classified_positive:
                card.classes("bg-green-200 ")
            else:
                card.classes("bg-red-200 ")

            # ui.label(message)
            with ui.column() as col:
                col.classes("flex justify-center w-full ")
                self._add_avatar(actually_positive, classified_positive)

                with ui.row() as buttons:
                    buttons.classes("flex justify-around w-full ")
                    ui.button("Weiter", on_click=lambda: dialog.submit("continue"))
                    ui.button("Beenden", on_click=lambda: dialog.submit("quit"))

        selection = await dialog

        if selection == "continue":
            self._update_text()
            self.callbacks.set_user_penalty(self.user, False)
            logger.info("no penalty")

        elif selection == "quit":
            ui.open("/")
            self.callbacks.set_user_penalty(self.user, False)
            logger.info("no penalty")

        else:
            ui.open("/")

    def _update_stats(self, classification: bool, true: bool) -> None:
        binary_stats_this_round = BinaryStats(
            float(true and classification),
            float(true and not classification),
            float(not true and classification),
            float(not true and not classification)
        )
        print("binary_stats_this_round")
        print(binary_stats_this_round)

        last_binary_stats_user = BinaryStats(
            self.user.true_positives,
            self.user.true_negatives,
            self.user.false_positives,
            self.user.false_negatives
        )
        print("last_binary_stats_user")
        print(last_binary_stats_user)

        new_binary_stats_user = (
                (binary_stats_this_round * self.points +
                 (last_binary_stats_user * (self.max_points - self.points))
                 ) / self.max_points)
        print(f"new_binary_stats_user ({self.points}/{self.max_points})")
        print(new_binary_stats_user)

        self.callbacks.update_user_state(
            self.user,
            new_binary_stats_user.true_positives, new_binary_stats_user.false_positives,
            new_binary_stats_user.true_negatives, new_binary_stats_user.false_negatives
        )
        print("binary_stats_session")
        print(self.binary_stats_session)

        self.binary_stats_session += binary_stats_this_round
        print("updated binary_stats_session")
        print(self.binary_stats_session)

    async def _submit(self, interactive_text: InteractiveText) -> None:
        print("submitting...")

        identity_file = await get_from_local_storage("identity_file")
        if identity_file is not None and os.path.isfile(identity_file):
            os.remove(identity_file)

        tags = interactive_text.selected_tags
        snippet_id = interactive_text.snippet.db_id

        actually_positive = interactive_text.snippet.is_bot
        classified_positive = len(tags) >= 1
        true = actually_positive == classified_positive

        self.user.recent_snippet_ids.append(snippet_id)

        self._update_stats(classified_positive, true)

        if classified_positive:
            self.callbacks.update_markers(tags, true)

        await self._feedback_dialog(actually_positive, classified_positive, interactive_text)

    def button_green(self) -> None:
        self.submit_button.props("color=positive")

    def button_red(self) -> None:
        self.submit_button.props("color=negative")

    async def create_content(self) -> None:
        logger.info("Game page")

        await self.client.connected()
        await self._check_user()
        await self._apply_penalty(self.user)

        header_classes = "text-2xl font-semibold text-center py-2 "

        with ui.element("div") as main_container:
            main_container.classes("mx-8 ")
            header = ui.label("Finde Hinweise auf KI!")
            header.classes(header_classes)

            await self._add_text_element()

            self._add_timing()

            with ui.row() as stats_row:
                stats_row.classes("flex justify-around w-full my-8 ")
                self._add_stats()

            self.submit_button = ui.button(
                self.submit_human,
                on_click=lambda: self._submit(self.interactive_text)
            )
            self.submit_button.classes("submit w-full ")

        self._init_javascript(f"c{self.submit_button.id}")
        self._update_text()
