import os
import random

from nicegui import app, ui

from src.dataobjects import Snippet
from src.gui.elements.interactive_text import InteractiveText
from src.gui.frame import create_footer


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


def submit(user_name: str, snippet: Snippet, points: int) -> None:
    identity_file = app.storage.user.pop("identity_file", None)
    if identity_file is not None:
        os.remove(identity_file)

    print(f"{user_name} assumed {hash(snippet)} as HUMAN with {points} points")
    # update stats
    #   if is_bot:
    #       register as gullible
    ui.open("/game")


def game_content() -> None:
    user_name = app.storage.user.get("user_name", None)
    if user_name is None:
        ui.open("/")
        return

    with ui.header(elevated=True):
        link_home = ui.link("home", "/")
        label_title = ui.label(f"{user_name}: Spot the Bot")

    points = 25
    snippet = next_snippet(user_name)
    interactive_text = InteractiveText(snippet)

    with ui.column() as column:
        text_display = interactive_text.get_content()

        text_points = ui.markdown(f"{points} points remaining")

        with ui.row() as row:
            # retrieve stats
            text_paranoid = ui.markdown("paranoid")
            element_diagram = ui.element()
            text_gullible = ui.markdown("gullible")

    submit_button = ui.button(interactive_text.submit_human, on_click=lambda: submit(user_name, snippet, points))
    submit_button.classes("w-full justify-center")

    async def init_tag_count() -> None:
        url = await ui.run_javascript(f'new URL(window.location.href)', respond=True)
        if not url.endswith("/game"):
            return
        await ui.run_javascript("window.tag_count = {};", respond=False)
        await ui.run_javascript(f"window.submit_button = document.getElementById('c{submit_button.id}');", respond=False)
        await ui.run_javascript("console.log('init finished')", respond=False)

    app.on_connect(init_tag_count)
    create_footer()

    def increment_counter() -> None:
        nonlocal points
        if 5 < points:
            points -= 1
        else:
            timer.deactivate()
        text_points.content = f"{points} points remaining"

    timer = ui.timer(1, increment_counter)

