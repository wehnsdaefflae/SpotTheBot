# coding=utf-8
import dataclasses
import random
import re
from typing import Callable, Coroutine

from fastapi import FastAPI
from nicegui import ui, app
from nicegui.elements.label import Label

from misc import hex_color_segmentation
from names import generate_name


@dataclasses.dataclass(frozen=True)
class Snippet:
    source: str
    content: str


class InteractiveText:
    def __init__(self, snippet: Snippet):
        self.submit_human = "I am sure it is fine..."
        self.submit_bot = "It is a bot!"
        self.snippet = snippet
        self.signs_dict = get_signs()
        self.colorized_signs = colorize(self.signs_dict)
        self.legend_tags = dict()
        self.content = self._generate_content()
        self.legend = None

    def _generate_content(self) -> ui.column:
        lines = self.snippet.content.split("\n")

        with ui.column() as main_text_content:
            ui.markdown(f"SOURCE: {self.snippet.source}")

            with ui.column() as text_content:
                for line_number, each_line in enumerate(lines):
                    with ui.row() as text_content_clickable:
                        for each_word in re.split(" ", each_line):
                            if len(each_word) < 1:
                                continue

                            each_word = each_word.strip()
                            label_word = ui.label(each_word)

                            label_word.on("click", lambda event: self._click_event(event.sender))
                            label_word.sus_sign = None
                            label_word.classes("cursor-pointer")

            with ui.row() as self.legend:
                for each_tag, each_color in self.colorized_signs:
                    each_label = ui.label(each_tag)
                    each_label.style(add=f"background-color: {each_color};")
                    self.legend_tags[each_tag] = each_label
                    each_label.set_visibility(False)

        return main_text_content

    async def _click_event(self, word_label: ui.label) -> None:
        if word_label.sus_sign is None:
            signs_popular = self.colorized_signs[:5]
            signs_rest = self.colorized_signs[5:]
            tag_word = self._get_tagging(word_label)
            with ui.menu() as menu:
                for each_sign, each_color in signs_popular:
                    each_item = ui.menu_item(each_sign, on_click=lambda _, sign=each_sign, color=each_color: tag_word(sign, None, color))
                    each_item.style(add=f"background-color: {each_color};")

                ui.separator()
                with ui.row() as row:
                    input_label = ui.input("something else...", autocomplete=[each_sign for each_sign, _ in signs_rest])
                    ui.button("submit", on_click=lambda _: self._rare_tag(word_label, input_label.value, signs_rest, menu))

            menu.move(word_label)
            menu.open()

        else:
            await self.decrement_tagged_word_count(word_label.sus_sign)
            word_label.default_slot.children.clear()
            word_label.style(remove="background-color:;")
            word_label.sus_sign = None

    def _get_tagging(self, label_word: ui.label) -> Callable[[str, ui.menu | None, str], Coroutine[None, None, None]]:
        async def _tag_word(tag: str, menu: ui.menu | None, color: str = "black") -> None:
            print(label_word.text + " ist zu " + tag)
            label_word.style(add=f"background-color: {color};")
            await ui.run_javascript(f"console.log(\"colorizing {color}\"); ", respond=False)
            label_word.sus_sign = tag
            await self.increment_tagged_word_count(tag)
            if menu is not None:
                menu.close()

        return _tag_word

    async def _rare_tag(self, word_label: ui.label, tag: str, rest_colorized: tuple[tuple[str, str], ...], menu: ui.menu | None) -> None:
        tag_dict = {each_tag: each_color for each_tag, each_color in rest_colorized}
        color = tag_dict.get(tag, "grey")
        tag_word = self._get_tagging(word_label)
        await tag_word(tag, menu, color)

    def get_content(self) -> ui.column:
        return self.content

    async def increment_tagged_word_count(self, tag: str) -> None:
        await ui.run_javascript(f"console.log(\"incrementing '{tag}'...\"); ", respond=False)

        js = (
            f"if (window.tag_count['{tag}']) {{",
            f"    window.tag_count['{tag}']++;",
            "} else {",
            f"    window.tag_count['{tag}'] = 1;",
            "}"
        )
        js_concatenated = "\n".join(js)
        await ui.run_javascript(js_concatenated, respond=False)

        js_line = f"window.submit_button.children[1].children[0].innerText = '{self.submit_bot}';"
        await ui.run_javascript(js_line, respond=False)

        tag_legend = self.legend_tags.get(tag)
        if tag_legend is not None:
            c = await self.get_tag_count(tag)
            tag_legend.set_visibility(c >= 1)

    async def get_tag_count(self, tag: str) -> int:
        tag_count_str = await ui.run_javascript(f"window.tag_count['{tag}'] ? window.tag_count['{tag}'] : 0", respond=True)
        return tag_count_str

    async def decrement_tagged_word_count(self, tag: str) -> None:
        # c = await self.get_tag_count(tag)
        await ui.run_javascript(f"console.log(\"decrementing '{tag}'...\"); ", respond=False)

        js = (
            f"window.tag_count['{tag}']--;",
            "let sum = 0;",
            "for (let key in window.tag_count) {",
            "    sum += window.tag_count[key];",
            "}",
            "if (sum === 0) {",
            f"    window.submit_button.children[1].children[0].innerText = '{self.submit_human}';",
            "}",
        )
        await ui.run_javascript("\n".join(js), respond=False)
        tag_legend = self.legend_tags.get(tag)
        if tag_legend is not None:
            c = await self.get_tag_count(tag)
            tag_legend.set_visibility(c >= 1)


def get_random_name() -> str:
    name = generate_name()
    return name
    # return f"[name {random.randint(1, 100)}]"


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
    # update stats
    #   if is_bot:
    #       register as gullible
    ui.open("/game")


def get_signs() -> dict[str, int]:
    return {
        "ausweichend": 523,
        "zu allgemein": 762,
        "abgedroschen": 304,
        "unlogisch": 947,
        "unverständlich": 665,
        "künstlich": 238,
        "monoton": 489,
        "redundant": 956,
        "langweilig": 112,
        "unpräzise": 839,
        "stereotyp": 721,
        "formelhaft": 596,
        "gekünstelt": 381,
        "unspezifisch": 428,
        "wiederholt": 710,
        "unzusammenhängend": 201
    }


def colorize(signs_dict: dict[str, int]) -> tuple[tuple[str, str], ...]:
    color_generator = hex_color_segmentation(.75)
    signs = sorted(signs_dict, key=signs_dict.get, reverse=True)
    return tuple((each_sign, next(color_generator)) for each_sign in signs)


@ui.page("/game")
def game_page() -> None:
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
        label_name.classes("cursor-pointer")
        label_name.on("click", lambda: randomize_name(label_name))

        create_footer()


def run(host_app: FastAPI) -> None:
    ui.run_with(
        host_app,
        title="Spot the Bot", storage_secret="secret",  # NOTE setting a secret is optional but allows for persistent storage per user
    )
