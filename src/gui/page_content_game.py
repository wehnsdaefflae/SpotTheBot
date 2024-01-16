from __future__ import annotations
import os
import dataclasses

from loguru import logger
from nicegui import ui, Client

from src.dataobjects import ViewCallbacks, User
from src.gui.elements.content_class import ContentPage
from src.gui.elements.dialogs import result_dialog, info_dialog
from src.gui.elements.interactive_text import InteractiveText
from src.gui.tools import get_from_local_storage


@dataclasses.dataclass
class BinaryStats:
    true_positives: float = 0.
    true_negatives: float = 0.
    false_positives: float = 0.
    false_negatives: float = 0.

    def clear(self) -> None:
        self.true_positives = 0.
        self.true_negatives = 0.
        self.false_positives = 0.
        self.false_negatives = 0.

    @property
    def actually_positive(self) -> float:
        return self.true_positives + self.false_negatives

    @property
    def actually_negative(self) -> float:
        return self.true_negatives + self.false_positives

    @property
    def classified_positive(self) -> float:
        return self.true_positives + self.false_positives

    @property
    def classified_negative(self) -> float:
        return self.true_negatives + self.false_negatives

    @property
    def total(self) -> float:
        return self.actually_positive + self.actually_negative

    @property
    def accuracy(self) -> float:
        if 0. >= self.total:
            return 0.
        return (self.true_positives + self.true_negatives) / self.total

    @property
    def precision(self) -> float:
        if 0. >= self.classified_positive:
            return 0.
        return self.true_positives / self.classified_positive

    @property
    def recall(self) -> float:
        if 0. >= self.actually_positive:
            return 0.
        return self.true_positives / self.actually_positive

    @property
    def true_positive_rate(self) -> float:
        if 0. >= self.actually_positive:
            return 0.
        return self.true_positives / self.actually_positive

    @property
    def true_negative_rate(self) -> float:
        if 0. >= self.actually_negative:
            return 0.
        return self.true_negatives / self.actually_negative

    @property
    def false_positive_rate(self) -> float:
        if 0. >= self.actually_negative:
            return 0.
        return self.false_positives / self.actually_negative

    @property
    def false_negative_rate(self) -> float:
        if 0. >= self.actually_positive:
            return 0.
        return self.false_negatives / self.actually_positive

    @property
    def f1(self) -> float:
        precision_plus_recall = self.precision + self.recall
        if 0. >= precision_plus_recall:
            return 0.
        return 2. * self.precision * self.recall / precision_plus_recall

    def __str__(self) -> str:
        return (
            f"tp: {self.true_positives:.2f}, "
            f"tn: {self.true_negatives:.2f}, "
            f"fp: {self.false_positives:.2f}, "
            f"fn: {self.false_negatives:.2f}"
        )

    def __add__(self, other: BinaryStats) -> BinaryStats:
        return BinaryStats(
            self.true_positives + other.true_positives,
            self.true_negatives + other.true_negatives,
            self.false_positives + other.false_positives,
            self.false_negatives + other.false_negatives
        )

    def __iadd__(self, other: BinaryStats) -> BinaryStats:
        self.true_positives += other.true_positives
        self.true_negatives += other.true_negatives
        self.false_positives += other.false_positives
        self.false_negatives += other.false_negatives
        return self

    def __mul__(self, other: float) -> BinaryStats:
        return BinaryStats(
            self.true_positives * other,
            self.true_negatives * other,
            self.false_positives * other,
            self.false_negatives * other
        )

    def __imul__(self, other: float) -> BinaryStats:
        self.true_positives *= other
        self.true_negatives *= other
        self.false_positives *= other
        self.false_negatives *= other
        return self

    def __rmul__(self, other: float) -> BinaryStats:
        return self * other

    def __truediv__(self, other: float) -> BinaryStats:
        return BinaryStats(
            self.true_positives / other,
            self.true_negatives / other,
            self.false_positives / other,
            self.false_negatives / other
        )

    def __itruediv__(self, other: float) -> BinaryStats:
        self.true_positives /= other
        self.true_negatives /= other
        self.false_positives /= other
        self.false_negatives /= other
        return self

    def __rtruediv__(self, other: float) -> BinaryStats:
        return self / other


class GameContent(ContentPage):
    def __init__(self, client: Client, callbacks: ViewCallbacks) -> None:
        super().__init__(client, callbacks)
        self.binary_stats_session = BinaryStats()

        self.submit_human = "I am sure it is fine..."
        self.submit_bot = "It is a bot!"

        self.min_points = 5
        self.points = self.max_points = -1

        self.avatar_container: ui.element | None = None

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

        print(f"{self.points} points")
        print(f"{self.max_points} max_points")

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

            await info_dialog("PENALIZED!")

        else:
            self.callbacks.set_user_penalty(user, True)
            logger.info("Setting penalty.")

    async def _add_text_element(self) -> None:
        self.interactive_text = InteractiveText(lambda: self.callbacks.get_next_snippet(self.user))
        self.interactive_text.generate_content()

    def _update_text(self) -> None:
        self.interactive_text.update_content()
        self.interactive_text.reset_tagged_word_count()
        # reset button label
        js = (
            "window.spotTheBot.submit_button.children[1].children[0].innerText = '" + self.submit_human + "';"
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
        with ui.row():
            ui.label().bind_text_from(self.binary_stats_session, "false_negatives")
            ui.label("/")
            ui.label().bind_text_from(self.binary_stats_session, "actually_positive")
            ui.label("Bots")

        with ui.row():
            ui.label().bind_text_from(self.binary_stats_session, "false_positives")
            ui.label("/")
            ui.label().bind_text_from(self.binary_stats_session, "actually_negative")
            ui.label("Menschen")

    def _add_avatar(self) -> None:
        state = "2"  # 2 happy, 0 sad, 1 angry
        if (
                self.binary_stats_session.false_positive_rate >= .2 and
                self.binary_stats_session.false_positive_rate >= self.binary_stats_session.false_negative_rate):
            state = "1"
        elif (
                self.binary_stats_session.false_negative_rate >= .2 and
                self.binary_stats_session.false_negative_rate >= self.binary_stats_session.false_positive_rate):
            state = "0"

        with ui.image(f"assets/images/portraits/{self.user.face.source_id}-{state}.png") as image:
            image.style("image-rendering: pixelated;")

        emotion = "ᕕ( ᐛ )ᕗ"
        if state == "0":
            emotion = "(◡︵◡)"
        elif state == "1":
            emotion = "(╯°□°)╯︵ ┻━┻"
        with ui.label(f"{emotion}") as name:
            name.classes("text-center text-base ")
            pass

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
            self._update_text()

            self._add_timing()

            with ui.row() as stats_row:
                stats_row.classes("flex justify-around w-full ")
                with ui.column() as col:
                    ui.label("Falsch erkannt: ")
                    self._add_stats()

                with ui.element("div").classes("w-20 md:w-40 rounded ") as self.avatar_container:
                    self._add_avatar()

            submit_button = ui.button(
                self.submit_human,
                on_click=lambda: self._submit(self.interactive_text)
            )
            submit_button.classes("submit w-full ")

        self._init_javascript(f"c{submit_button.id}")

    async def _feedback_dialog(
            self, actually_positive: bool, classified_positive: bool, interactive_text: InteractiveText) -> None:
        base_truth = "BOT" if actually_positive else "HUMAN"
        classification = "BOT" if classified_positive else "HUMAN"
        selection = await result_dialog(
            f"{self.user.public_name} classified {base_truth} text "
            f"{interactive_text.snippet.db_id} as {classification} "
            f"with {self.points} points certainty of {self.max_points} total."
        )
        if selection == "continue":
            self._update_text()
            self.callbacks.set_user_penalty(self.user, False)
            self.avatar_container.clear()
            with self.avatar_container:
                self._add_avatar()
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
