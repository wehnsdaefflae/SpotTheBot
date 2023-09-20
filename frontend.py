# coding=utf-8
import dataclasses
import random

from fastapi import FastAPI
from nicegui import ui, app
from nicegui.elements.dialog import Dialog
from nicegui.elements.label import Label


def get_random_name() -> str:
    return f"[name {random.randint(1, 100)}]"


def randomize_name(label: Label) -> None:
    label.text = get_random_name()


def create_footer() -> None:
    with ui.footer() as footer:
        with ui.row() as row:
            label_aces = ui.link("check out top aces", "/aces")
            label_results = ui.link("check out results", "/results")
            label_about = ui.link("about", "/about")


def start_game(user_name: str) -> None:
    app.storage.user["user_name"] = user_name
    ui.open("/game")


@ui.page("/aces")
def aces_page() -> None:
    with ui.header(elevated=True):
        link_home = ui.link("home", "/")
        label_title = ui.label("Top Aces")

    for i in range(10):
        ui.label(f"[ace {i + 1}] [accuracy]")

    create_footer()


@ui.page("/results")
def results_page() -> None:
    with ui.header(elevated=True):
        link_home = ui.link("home", "/")
        label_title = ui.label("Results")

    for i in range(10):
        ui.label(f"[result {i + 1}] [accuracy]")

    text_example = ui.markdown("""Die ADF-RDA ist 1998 in der heutigen Form aus einer Fusion zwischen verschiedenen kleineren Parteien und der ADF mit dem 
    traditionsreichen Rassemblement Démocratique Africain, <span style="background-color: red;">RDA</span> hervorgegangen, in dessen programmatischer Tradition sie 
    sich bis heute sieht. Die ADF-RDA ist von der Wählerstärke her betrachtet eine der konstantesten Parteien Burkina Fasos. Bereits an den Parlamentswahlen vom 24. 
    Mai 1992 und 11. Mai 1997, welche von der ADF und dem RDA noch unabhängig voneinander bestritten wurden, kamen sie zusammen auf einen ähnlichen Wähleranteil von 
    rund 13 %.""")

    create_footer()


@ui.page("/about")
def about_page() -> None:
    with ui.header(elevated=True):
        link_home = ui.link("home", "/")
        label_title = ui.label("About")

    text_example = ui.markdown("bla bla bla")
    donate_label = ui.markdown("donate, enter api key, etc")
    api_text = ui.textarea("api key")

    create_footer()


@dataclasses.dataclass(frozen=True)
class Snippet:
    source: str
    content: str


def next_snippet(user_name: str) -> Snippet:
    content = (
        f"""
        TEXT {random.randint(0, 100)}:
        
        Die ADF-RDA ist 1998 in der heutigen Form aus einer Fusion zwischen verschiedenen kleineren Parteien und der ADF mit dem traditionsreichen Rassemblement 
        Démocratique Africain, <span style=\"background-color: red;\">RDA</span> hervorgegangen, in dessen programmatischer Tradition sie sich bis heute sieht. Die 
        ADF-RDA ist von der Wählerstärke her betrachtet eine der konstantesten Parteien Burkina Fasos. Bereits an den Parlamentswahlen vom 24. Mai 1992 und 11. Mai 
        1997, welche von der ADF und dem RDA noch unabhängig voneinander bestritten wurden, kamen sie zusammen auf einen ähnlichen Wähleranteil von rund 13 %.
        """
    )
    return Snippet(
        source="Wikipedia",
        content=content
    )


def assumed_human(user_name: str, snippet_id: int, points: int) -> None:
    print(f"{user_name} assumed {snippet_id} as HUMAN with {points} points")
    # update stats
    ui.open("/game")


def assumed_bot(user_name: str, snippet_id: int, points: int) -> None:
    print(f"{user_name} assumed {snippet_id} as BOT with {points} points")

    def update_stats(_dialog: Dialog) -> None:
        # update stats
        _dialog.close()
        ui.open("/game")

    with ui.dialog() as dialog, ui.card():
        ui.label("Give reasons why you think this is a bot")
        ui.button("Close", on_click=lambda: update_stats(dialog))

    dialog.open()


@ui.page("/game")
def game_page() -> None:
    user_name = app.storage.user.get("user_name", None)
    if user_name is None:
        ui.open("/")
        return

    with ui.header(elevated=True):
        link_home = ui.link("home", "/")
        label_title = ui.label(f"{user_name}: Spot the Bot")

    word_counter = 0
    points = 100
    snippet = next_snippet(user_name)
    # words = snippet.content.split(" ")

    with ui.column() as column:
        text_context = ui.markdown(f"SOURCE: {snippet.source}")
        text_content = ui.markdown(snippet.content)

        text_points = ui.markdown(f"{points} points remaining")

        with ui.row() as row:
            # retrieve stats
            text_paranoid = ui.markdown("paranoid")
            element_diagram = ui.element()
            text_gullible = ui.markdown("gullible")

        with ui.row() as row:
            button_bot = ui.button("BOT", on_click=lambda: assumed_bot(user_name, hash(snippet), points))
            button_human = ui.button("HUMAN", on_click=lambda: assumed_human(user_name, hash(snippet), points))

    create_footer()

    def increment_counter() -> None:
        nonlocal word_counter, points
        word_counter += 1
        if 5 < points:
            points -= 1
        text_points.content = f"{points} points remaining"
        # text_content.content = " ".join(words[:word_counter])

    timer = ui.timer(.25, increment_counter)


@ui.page("/")
def index_page() -> None:
    with ui.column() as column:
        title_label = ui.label("Look out for")
        title_label.classes("text-h4 font-bold text-grey-8")

        for i in range(4):
            each_indicator_label = ui.label(f"[indicator {i + 1}] [accuracy]")

        user_name = app.storage.user.get("user_name", get_random_name())

        button_start = ui.button("SPOT THE BOT", on_click=lambda: start_game(label_name.text))

        label_welcome = ui.label(f"as")
        label_name = ui.label(user_name)
        label_name.on("click", lambda: randomize_name(label_name))

        create_footer()


def run(host_app: FastAPI) -> None:
    ui.run_with(
        host_app,
        title="Spot the Bot", storage_secret="secret",  # NOTE setting a secret is optional but allows for persistent storage per user
    )
