import os
import random

from loguru import logger
from nicegui import app, ui, Client

from src.dataobjects import Snippet, ViewCallbacks
from src.gui.elements.content_class import ContentPage
from src.gui.elements.dialogs import persistent_dialog
from src.gui.elements.frame import frame
from src.gui.elements.interactive_text import InteractiveText
from src.gui.tools import get_from_local_storage


def next_snippet(user_name: str | None = None) -> Snippet:
    content = (
        f"TEXT {random.randint(0, 100)}:\n"
        f"\n"
        f"Die ADF-RDA ist 1998 in der heutigen Form aus einer Fusion zwischen verschiedenen kleineren Parteien und der ADF mit dem traditionsreichen Rassemblement "
        f"Démocratique Africain, RDA hervorgegangen, in dessen programmatischer Tradition sie sich bis heute sieht. Die ADF-RDA ist von der Wählerstärke her betrachtet "
        f"eine der konstantesten Parteien Burkina Fasos. Bereits an den Parlamentswahlen vom 24. Mai 1992 und 11. Mai 1997, welche von der ADF und dem RDA noch "
        f"unabhängig voneinander bestritten wurden, kamen sie zusammen auf einen ähnlichen Wähleranteil von rund 13 %."
    )
    return Snippet(
        source="Wikipedia",
        text=content,
        is_bot=False
    )


async def submit(user_name: str, snippet: Snippet, points: int) -> None:
    identity_file = await get_from_local_storage("identity_file")
    if identity_file is not None and os.path.isfile(identity_file):
        os.remove(identity_file)

    await persistent_dialog(f"{user_name} assumed {hash(snippet)} as HUMAN with {points} points")
    ui.open("/game")


class GameContent(ContentPage):
    def __init__(self, client: Client, callbacks: ViewCallbacks) -> None:
        super().__init__(client, callbacks)
        self.points = 25
        self.text_points = None
        self.timer = None

    @staticmethod
    async def init_tag_count(button_id: int) -> None:
        url = await ui.run_javascript(f'new URL(window.location.href)')
        if not url.endswith("/game"):
            return
        _ = ui.run_javascript("window.tag_count = {};")
        _ = ui.run_javascript(f"window.submit_button = document.getElementById('c{button_id}');")
        _ = ui.run_javascript("console.log('init finished')")

    def increment_counter(self) -> None:
        if 5 < self.points:
            self.points -= 1
        else:
            self.timer.deactivate()

        self.text_points.content = f"{self.points} points remaining"

    async def create_content(self) -> None:
        logger.info("Game page")

        await self.client.connected()

        # app.on_connect(self.init_tag_count)

        name_hash = await get_from_local_storage("name_hash")
        if name_hash is None:
            ui.open("/")

        snippet = next_snippet(name_hash)

        with frame() as _frame:
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
                interactive_text.submit_human,
                on_click=lambda: submit(name_hash, snippet, self.points)
            )
            submit_button.classes("w-full justify-center")

            await GameContent.init_tag_count(submit_button.id)

        self.timer = ui.timer(1, self.increment_counter)
