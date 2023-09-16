# coding=utf-8
import random

from nicegui import ui, app
from nicegui.elements.label import Label


def generate_name(label: Label) -> None:
    label.text = f"[name {random.randint(1, 100)}]"


def log_in(user_name: str) -> None:
    app.storage.user["user_name"] = user_name
    ui.open("/")


def start_game() -> None:
    user_name = app.storage.user.get("user_name", None)
    ui.label(f"Hello {user_name}!")


def landing_page() -> None:
    title_label = ui.label("Look out for")
    title_label.classes("text-h4 font-bold text-grey-8")

    for i in range(4):
        each_indicator_label = ui.label(f"[indicator {i + 1}] [accuracy]")

    button_start = ui.button("SPOT THE BOT")
    label_as = ui.label("as")
    label_name = ui.label()
    generate_name(label_name)

    label_name.on("click", lambda: generate_name(label_name))
    button_start.on("click", lambda: log_in(label_name.text))

    with ui.row() as row:
        label_aces = ui.label("check out top aces")
        label_results = ui.label("check out results")


@ui.page("/")
def index_page() -> None:
    user_name = app.storage.user.get("user_name", None)
    with ui.column() as column:
        if user_name is None:
            landing_page()
        else:
            start_game()


def main() -> None:
    ui.run(title="Spot the Bot", storage_secret="secret")


if __name__ in {"__main__", "__mp_main__"}:
    main()
