import re
from collections import Counter
from typing import Callable, Coroutine

from nicegui import ui

from src.dataobjects import Snippet
from src.gui.dummies import get_signs
from src.gui.tools import colorize


class InteractiveText:
    def __init__(self, get_snippet: Callable[[], Snippet]):
        self.get_snippet = get_snippet
        self.snippet: Snippet | None = None

        self.signs_dict = get_signs()
        self.colorized_signs = colorize(self.signs_dict)
        self.legend_tags = dict()

        self._source_content = ""
        self._text_content: ui.column | None = None

        self.legend = None

        self.selected_tags = Counter()

    def _update_snippet_text(self, text: str) -> None:
        self._text_content.clear()
        lines = text.split("\n")
        with self._text_content:
            for line_number, each_line in enumerate(lines):
                with ui.row() as text_content_clickable:
                    text_content_clickable.classes("gap-y-0 ")
                    for each_word in re.split(" ", each_line):
                        if len(each_word) < 1:
                            continue

                        each_word = each_word.strip()
                        label_word = ui.label(each_word)
                        label_word.on("click", lambda event: self._click_event(event.sender))
                        label_word.sus_sign = None
                        label_word.classes("cursor-pointer ")
                        label_word.classes("word untagged ")

    def update_content(self) -> None:
        self.snippet = self.get_snippet()
        self._source_content = self.snippet.source
        # todo: replace with link to video
        self._update_snippet_text(self.snippet.text)

    def generate_content(self) -> ui.column:
        with ui.column() as main_column:
            main_column.classes("bg-gray-100 rounded-lg shadow-lg p-4 max-w-4xl mx-auto ")
            with ui.markdown() as source_text:
                source_text.classes("text-right text-sm text-gray-500 w-full ")
                source_text.bind_content(self, "_source_content")

            ui.separator()

            ui.label("“").classes("text-9xl text-gray-400 h-8 ")

            with ui.column() as self._text_content:
                self._text_content.classes("text-xl max-w-prose mx-auto ")

            ui.label("”").classes("text-9xl text-gray-400 w-full text-right h-8 ")

            with ui.row() as self.legend:
                self.legend.classes("legend h-16 ")
                for each_tag, each_color in self.colorized_signs:
                    each_label = ui.label(each_tag)
                    each_label.classes("legend-item item-01 ")
                    # todo: custom labels are not colored correctly
                    each_label.style(add=f"background-color: {each_color};")
                    self.legend_tags[each_tag] = each_label
                    each_label.set_visibility(False)

        return main_column

    async def _click_event(self, word_label: ui.label) -> None:
        if word_label.sus_sign is None:
            word_label.classes("tagged")
            signs_popular = self.colorized_signs[:5]
            signs_rest = self.colorized_signs[5:]
            tag_word = self._get_tagging(word_label)
            with ui.menu() as menu:
                for each_sign, each_color in signs_popular:
                    each_item = ui.menu_item(
                        each_sign,
                        on_click=lambda _, sign=each_sign, color=each_color: tag_word(sign, None, color)
                    )
                    each_item.style(add=f"background-color: {each_color};")

                ui.separator()
                with ui.row() as row:
                    input_label = ui.input(
                        "something else...",
                        autocomplete=[each_sign for each_sign, _ in signs_rest]
                    )
                    input_label.on(
                        "change",
                        lambda: self._rare_tag(word_label, input_label.value, signs_rest, menu)
                    )

            menu.move(word_label)
            menu.open()

        else:
            await self.decrement_tagged_word_count(word_label.sus_sign)
            word_label.default_slot.children.clear()
            word_label.classes(remove="tagged")
            word_label.style(remove="background-color:;")
            word_label.sus_sign = None

    def _get_tagging(self, label_word: ui.label) -> Callable[[str, ui.menu | None, str], Coroutine[None, None, None]]:
        async def _tag_word(tag: str, menu: ui.menu | None, color: str = "black") -> None:
            print(label_word.text + " ist zu " + tag)
            label_word.style(add=f"background-color: {color};")
            _ = ui.run_javascript(f"console.log(\"colorizing {color}\");")
            label_word.sus_sign = tag
            await self.increment_tagged_word_count(tag)
            if menu is not None:
                menu.close()

        return _tag_word

    async def _rare_tag(
            self,
            word_label: ui.label,
            tag: str,
            rest_colorized: tuple[tuple[str, str], ...],
            menu: ui.menu | None) -> None:

        tag_dict = {each_tag: each_color for each_tag, each_color in rest_colorized}
        color = tag_dict.get(tag, "grey")
        tag_word = self._get_tagging(word_label)
        await tag_word(tag, menu, color)

    def reset_tagged_word_count(self) -> None:
        ui.run_javascript(
            "window.spotTheBot.tag_count = {};"
        )
        self.selected_tags.clear()
        for each_label in self.legend_tags.values():
            each_label.set_visibility(False)

    async def increment_tagged_word_count(self, tag: str) -> None:
        count = await ui.run_javascript(f"window.spotTheBot.increment('{tag}');")
        self.selected_tags[tag] += 1

        tag_legend = self.legend_tags.get(tag)
        if tag_legend is not None:
            tag_legend.set_visibility(count >= 1)

    async def decrement_tagged_word_count(self, tag: str) -> None:
        count = await ui.run_javascript(f"window.spotTheBot.decrement('{tag}');")
        count_local = self.selected_tags.get(tag)
        if count_local is not None:
            if 1 >= count_local:
                del self.selected_tags[tag]
            else:
                self.selected_tags[tag] = count_local - 1

        tag_legend = self.legend_tags.get(tag)
        if tag_legend is not None:
            tag_legend.set_visibility(count >= 1)
