import os

from loguru import logger
from nicegui import ui, Client

from src.dataobjects import ViewCallbacks
from src.gui.elements.content_class import ContentPage
from src.gui.elements.dialogs import result_dialog, info_dialog
from src.gui.elements.interactive_text import InteractiveText
from src.gui.tools import get_from_local_storage


class GameContent(ContentPage):
    def __init__(self, client: Client, callbacks: ViewCallbacks) -> None:
        super().__init__(client, callbacks)
        # richtig erkannt: bot correctly identified as bot: true positives / positives
        # falsch erkannt: human incorrectly identified as bot: false positives / negatives
        self.true_positives = self.false_positives = self.true_negatives = self.false_negatives = 0
        self.actually_positive = self.actually_negative = 0

        self.timer: ui.timer | None = None
        self.points = self.max_points = -1
        self.text_points = None
        self.submit_human = "I am sure it is fine..."
        self.submit_bot = "It is a bot!"
        self.user = None

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

    async def _submit(self, interactive_text: InteractiveText) -> None:
        identity_file = await get_from_local_storage("identity_file")
        if identity_file is not None and os.path.isfile(identity_file):
            os.remove(identity_file)

        positive = len(interactive_text.selected_tags) >= 1
        true = interactive_text.snippet.is_bot == positive
        if interactive_text.snippet.is_bot:
            self.actually_positive += 1
        else:
            self.actually_negative += 1

        snippet_id = interactive_text.snippet.db_id
        self.user.recent_snippet_ids.append(snippet_id)

        true_positive_value = int(true and positive)
        false_positive_value = int(not true and positive)
        true_negative_value = int(true and not positive)
        false_negative_value = int(not true and not positive)

        last_tp = self.user.true_positives
        last_fp = self.user.false_positives
        last_tn = self.user.true_negatives
        last_fn = self.user.false_negatives

        true_positive_scaled = (
                true_positive_value * self.points + (last_tp * (self.max_points - self.points))
                / self.max_points
        )
        false_positive_scaled = (
                false_positive_value * self.points + (last_fp * (self.max_points - self.points))
                / self.max_points
        )
        true_negative_scaled = (
                true_negative_value * self.points + (last_tn * (self.max_points - self.points))
                / self.max_points
        )
        false_negative_scaled = (
                false_negative_value * self.points + (last_fn * (self.max_points - self.points))
                / self.max_points
        )

        self.callbacks.update_user_state(
            self.user, true_positive_scaled, false_positive_scaled, true_negative_scaled, false_negative_scaled
        )

        self.true_positives += true_positive_value
        self.false_positives += false_positive_value

        self.true_negatives += true_negative_value
        self.false_negatives += false_negative_value

        tags = interactive_text.selected_tags

        base_truth = "BOT" if interactive_text.snippet.is_bot else "HUMAN"
        classification = "HUMAN" if len(tags) < 1 else "BOT"

        if len(tags) >= 1:
            self.callbacks.update_markers(tags, true)

        selection = await result_dialog(
            f"{self.user.public_name} classified {base_truth} text "
            f"{interactive_text.snippet.db_id} as {classification} "
            f"with {self.points} points certainty of {self.max_points} total."
        )

        if selection == "continue":
            interactive_text.update_content()
            await interactive_text.reset_tagged_word_count()
            snippet = interactive_text.snippet
            word_count = len(snippet.text.split())
            self.points = word_count // 4
            self.callbacks.set_user_penalty(self.user, False)
            logger.info("no penalty")

        elif selection == "quit":
            ui.open("/")
            self.callbacks.set_user_penalty(self.user, False)
            logger.info("no penalty")

        else:
            ui.open("/")

    async def create_content(self) -> None:
        logger.info("Game page")

        await self.client.connected()
        name_hash = await get_from_local_storage("name_hash")
        if name_hash is None:
            logger.warning("No name hash found, returning to start page.")
            ui.open("/")
            return

        self.user = self.callbacks.get_user(name_hash)
        penalize = self.user.penalty
        logger.info(f"This round penalty: {penalize}")

        if penalize:
            false_positives = self.user.false_positives + 5.
            false_negatives = self.user.false_negatives + 5.
            self.callbacks.update_user_state(self.user, 0, false_positives, 0, false_negatives)

            selection = await info_dialog("PENALIZED!")

        else:
            self.callbacks.set_user_penalty(self.user, True)
            logger.info("Setting penalty.")

        header_classes = "text-2xl font-semibold text-center py-2 "

        with ui.element("div") as main_container:
            main_container.classes("mx-8 ")
            header = ui.label("Finde Hinweise auf KI!")
            header.classes(header_classes)

            interactive_text = InteractiveText(lambda: self.callbacks.get_next_snippet(self.user))
            interactive_text.generate_content()
            interactive_text.update_content()

            snippet = interactive_text.snippet
            word_count = len(snippet.text.split())
            self.points = word_count // 4

            def _decrement_points() -> None:
                if 5 < self.points:
                    self.points -= 1
                else:
                    self.timer.deactivate()

            with ui.row() as points:
                points.classes("flex justify-center text-base ")
                point_text = ui.label().bind_text(self, "points")
                self.text_points = ui.label(" Punkte übrig")

            self.timer = ui.timer(1, _decrement_points)

            with ui.row() as stats_row:
                stats_row.classes("flex justify-around ")
                with ui.column() as col:
                    ui.label("Falsch erkannt: ")
                    with ui.row():
                        ui.label().bind_text(self, "false_negatives")
                        ui.label("/")
                        ui.label().bind_text(self, "actually_positive")
                        ui.label("Bots")

                    with ui.row():
                        ui.label().bind_text(self, "false_positives")
                        ui.label("/")
                        ui.label().bind_text(self, "actually_negative")
                        ui.label("Menschen")

                with ui.element("div").classes("w-20 md:w-40 rounded ") as avatar_container:
                    state = "2"  # 2 happy, 0 sad, 1 angry
                    false_negative_rate = 0. if 0 >= self.actually_positive else self.false_negatives / self.actually_positive
                    false_positive_rate = 0. if 0 >= self.actually_negative else self.false_positives / self.actually_negative

                    if false_positive_rate >= .2 and false_positive_rate >= false_negative_rate:
                        state = "1"
                    elif false_negative_rate >= .2 and false_negative_rate >= false_positive_rate:
                        state = "0"

                    with ui.image(f"assets/images/portraits/{self.user.face.source_id}-{state}.png") as image:
                        pass

                    emotion = "kompetent :D"
                    if state == "0":
                        emotion = "naiv :.-("
                    elif state == "1":
                        emotion = "skrupellos D-:<"
                    with ui.label(f"{emotion}") as name:
                        name.classes("text-center text-base ")
                        pass

            submit_button = ui.button(
                self.submit_human,
                on_click=lambda: self._submit(interactive_text)
            )
            submit_button.classes("submit w-full ")

            self._init_javascript(f"c{submit_button.id}")
