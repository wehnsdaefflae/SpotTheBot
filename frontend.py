# coding=utf-8
import dataclasses
import random
import re
from typing import Callable, Coroutine

from fastapi import FastAPI
from nicegui import ui, app
from nicegui.elements.label import Label
from nicegui.events import ClickEventArguments


async def increment_tagged_word_count() -> None:
    await ui.run_javascript(
        f"window.tagged_word_count++; ", respond=False)

    await ui.run_javascript(
        f"window.submit_button.children[1].children[0].innerText = 'It is a bot!';", respond=False
    )


async def decrement_tagged_word_count() -> None:
    await ui.run_javascript("window.tagged_word_count = Math.max(tagged_word_count - 1, 0);", respond=False)
    await ui.run_javascript(
        "if (window.tagged_word_count < 1) {\n"
        "    window.submit_button.children[1].children[0].innerText = 'I am sure it is fine...';\n"
        "}", respond=False
    )



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
        f"TEXT {random.randint(0, 100)}:\n"
        f"\n"
        f"Die ADF-RDA ist 1998 in der heutigen Form aus einer Fusion zwischen verschiedenen kleineren Parteien und der ADF mit dem traditionsreichen Rassemblement "
        f"Démocratique Africain, RDA hervorgegangen, in dessen programmatischer Tradition sie sich bis heute sieht. Die ADF-RDA ist von der Wählerstärke her betrachtet "
        f"eine der konstantesten Parteien Burkina Fasos. Bereits an den Parlamentswahlen vom 24. Mai 1992 und 11. Mai 1997, welche von der ADF und dem RDA noch "
        f"unabhängig voneinander bestritten wurden, kamen sie zusammen auf einen ähnlichen Wähleranteil von rund 13 %."
    )
    return Snippet(
        source="Wikipedia",
        content=content
    )


def submit(user_name: str, snippet: Snippet, points: int) -> None:
    print(f"{user_name} assumed {hash(snippet)} as HUMAN with {points} points")
    global tagged_word_count, button_text
    tagged_word_count = 0
    button_text = "I'm sure it's fine..."

    # update stats
    #   if is_bot:
    #       register as gullible
    ui.open("/game")


def get_signs() -> list[str]:
    return [
        "ausweichend",
        "zu allgemein",
        "abgedroschen",
        "unlogisch",
        "unverständlich",
        "künstlich",
        "monoton",
        "redundant",
        "langweilig",
        "unpräzise",
        "stereotyp",
        "formelhaft",
        "gekünstelt",
        "unspezifisch",
        "wiederholt",
        "unzusammenhängend"
    ]


def get_tagging(label_word: ui.label) -> Callable[[ClickEventArguments], Coroutine[None, None, None]]:
    async def _tag_word(event: ClickEventArguments) -> None:
        print(label_word.text + " ist zu " + event.sender.text)
        label_word.style(add="background-color: red;")
        label_word.sus_sign = event.sender.text
        await increment_tagged_word_count()

    return _tag_word


async def click_event(event: ClickEventArguments) -> None:
    word_label = event.sender
    assert isinstance(word_label, ui.label)
    if word_label.sus_sign is None:
        signs = get_signs()
        tag_word = get_tagging(word_label)
        with ui.menu() as menu:
            for each_sign in signs:
                ui.menu_item(each_sign, on_click=tag_word)
            ui.separator()
            ui.menu_item("something else...", on_click=lambda: None)

        menu.move(word_label)
        menu.open()

    else:
        await decrement_tagged_word_count()
        word_label.default_slot.children.clear()
        word_label.style(remove="background-color: red;")
        word_label.sus_sign = None


def show_text(snippet: Snippet) -> ui.column:
    lines = snippet.content.split("\n")

    with ui.column() as text_content:
        for line_number, each_line in enumerate(lines):
            with ui.row() as text_content_clickable:
                for each_word in re.split(" ", each_line):
                    if len(each_word) < 1:
                        continue

                    each_word = each_word.strip()
                    label_word = ui.label(each_word)
                    label_word.on("click", lambda event: click_event(event))

                    label_word.sus_sign = None
                    label_word.classes("cursor-pointer")

    return text_content


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

    with ui.column() as column:
        text_context = ui.markdown(f"SOURCE: {snippet.source}")
        text_content = show_text(snippet)

        text_points = ui.markdown(f"{points} points remaining")

        with ui.row() as row:
            # retrieve stats
            text_paranoid = ui.markdown("paranoid")
            element_diagram = ui.element()
            text_gullible = ui.markdown("gullible")

        submit_button = ui.button("<empty>", on_click=lambda: submit(user_name, snippet, points))
        submit_button.classes("w-full justify-center")

    async def init_tag_count() -> None:
        await ui.run_javascript("window.tagged_word_count = 0;", respond=False)
        await ui.run_javascript(f"window.submit_button = document.getElementById('c{submit_button.id}');", respond=False)
        await decrement_tagged_word_count()

    app.on_connect(init_tag_count)
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
