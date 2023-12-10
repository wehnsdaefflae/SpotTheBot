import os

from loguru import logger
from nicegui import ui, Client

from src.dataobjects import ViewCallbacks
from src.gui.elements.content_class import ContentPage
from src.gui.elements.dialogs import result_dialog
from src.gui.elements.interactive_text import InteractiveText
from src.gui.tools import get_from_local_storage


class GameContent(ContentPage):
    def __init__(self, client: Client, callbacks: ViewCallbacks) -> None:
        super().__init__(client, callbacks)
        self.points = self.max_points = 25
        self.text_points = None
        self.timer = None

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

    def _decrement_points(self) -> None:
        if 5 < self.points:
            self.points -= 1
        else:
            self.timer.deactivate()

        self.text_points.content = f"{self.points} points remaining"

    async def _submit(self, interactive_text: InteractiveText, points: int, penalize: bool) -> None:
        identity_file = await get_from_local_storage("identity_file")
        if identity_file is not None and os.path.isfile(identity_file):
            os.remove(identity_file)

        if penalize:
            how_true = -1 * self.max_points // 2
            self.callbacks.update_user_state(self.user, interactive_text.snippet.is_bot, how_true, self.max_points)
            self.callbacks.set_user_penalty(self.user, False)

            selection = await result_dialog("PENALIZED!")

        else:
            correct = interactive_text.snippet.is_bot == (0 < len(interactive_text.selected_tags))

            snippet_id = interactive_text.snippet.db_id
            self.user.recent_snippet_ids.append(snippet_id)

            how_true = points * (int(correct) * 2 - 1)
            self.callbacks.update_user_state(self.user, interactive_text.snippet.is_bot, how_true, self.max_points)

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
            ui.open("/game")
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

        self.callbacks.set_user_penalty(self.user, True)
        logger.info("Setting penalty.")

        snippet = self.callbacks.get_next_snippet(self.user)

        word_count = len(snippet.text.split())
        self.max_points = self.points = word_count // 4

        interactive_text = InteractiveText(snippet)

        with ui.column() as column:
            text_display = interactive_text.get_content()

            self.text_points = ui.markdown(f"{self.points} points remaining")

            with ui.row() as row:
                # retrieve stats
                text_paranoid = ui.markdown("paranoid")
                element_diagram = ui.element()
                text_gullible = ui.markdown("gullible")

        submit_button = ui.button(
            self.submit_human,
            on_click=lambda: self._submit(interactive_text, self.points, penalize)
        )
        submit_button.classes("w-full justify-center")
        self._init_javascript(f"c{submit_button.id}")

        self.timer = ui.timer(1, self._decrement_points)

    async def _create_content(self) -> None:
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

        self.callbacks.set_user_penalty(self.user, True)
        logger.info("Setting penalty.")

        snippet = self.callbacks.get_next_snippet(self.user)

        word_count = len(snippet.text.split())
        self.max_points = self.points = word_count // 4

        interactive_text = InteractiveText(snippet)

        with ui.column() as column:
            text_display = interactive_text.get_content()

            self.text_points = ui.markdown(f"{self.points} points remaining")

            with ui.row() as row:
                # retrieve stats
                text_paranoid = ui.markdown("paranoid")
                element_diagram = ui.element()
                text_gullible = ui.markdown("gullible")

        submit_button = ui.button(
            self.submit_human,
            on_click=lambda: self._submit(interactive_text, self.points, penalize)
        )
        submit_button.classes("w-full justify-center")
        self._init_javascript(f"c{submit_button.id}")

        self.timer = ui.timer(1, self._decrement_points)
