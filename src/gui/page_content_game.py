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
        self.trues = self.falses = 0
        self.true_positives = self.false_positives = 0

        self.points = self.max_points = 25
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

    async def _submit(self, interactive_text: InteractiveText, points: int) -> None:
        identity_file = await get_from_local_storage("identity_file")
        if identity_file is not None and os.path.isfile(identity_file):
            os.remove(identity_file)

        correct = interactive_text.snippet.is_bot == (0 < len(interactive_text.selected_tags))

        snippet_id = interactive_text.snippet.db_id
        self.user.recent_snippet_ids.append(snippet_id)

        how_true = points * (int(correct) * 2 - 1)
        self.callbacks.update_user_state(self.user, interactive_text.snippet.is_bot, how_true, self.max_points)

        self.trues += int(interactive_text.snippet.is_bot)
        self.falses += int(not interactive_text.snippet.is_bot)

        self.true_positives += int(interactive_text.snippet.is_bot and correct)
        self.false_positives += int(not interactive_text.snippet.is_bot and not correct)

        tags = interactive_text.selected_tags

        base_truth = "BOT" if interactive_text.snippet.is_bot else "HUMAN"
        classification = "HUMAN" if len(tags) < 1 else "BOT"

        if len(tags) >= 1:
            self.callbacks.update_markers(tags, correct)

        selection = await result_dialog(
            f"{self.user.public_name} classified {base_truth} text "
            f"{interactive_text.snippet.db_id} as {classification} "
            f"with {points} points certainty of {self.max_points} total."
        )

        if selection == "continue":
            interactive_text.update_content()
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
            self.callbacks.update_user_state(self.user, True, -5, 10)
            self.callbacks.update_user_state(self.user, False, -5, 10)

            selection = await info_dialog("PENALIZED!")

        else:
            self.callbacks.set_user_penalty(self.user, True)
            logger.info("Setting penalty.")

        snippet = self.callbacks.get_next_snippet(self.user)

        word_count = len(snippet.text.split())
        max_points = word_count // 4

        header_classes = "text-2xl font-semibold text-center py-2 "

        with ui.element("div") as main_container:
            main_container.classes("mx-8 ")
            header = ui.label("Finde Hinweise auf KI!")
            header.classes(header_classes)

            interactive_text = InteractiveText(max_points, lambda: self.callbacks.get_next_snippet(self.user))
            interactive_text.generate_content()
            interactive_text.update_content()

            with ui.row() as stats_row:
                stats_row.classes("flex justify-between ")
                with ui.row():
                    ui.label("RICHTIG erkannt: ")
                    ui.label().bind_text(self, "true_positives")
                    ui.label("/")
                    ui.label().bind_text(self, "trues")
                    ui.label("Bots")

                with ui.row():
                    ui.label("FALSCH erkannt: ")
                    ui.label().bind_text(self, "false_positives")
                    ui.label("/")
                    ui.label().bind_text(self, "falses")
                    ui.label("Menschen")

            submit_button = ui.button(
                self.submit_human,
                on_click=lambda: self._submit(interactive_text, self.points)
            )
            submit_button.classes("submit w-full ")

            self._init_javascript(f"c{submit_button.id}")
