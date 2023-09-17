# coding=utf-8
import random

from nicegui import ui, app
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


@ui.page("/")
def index_page() -> None:
    with ui.column() as column:
        title_label = ui.label("Look out for")
        title_label.classes("text-h4 font-bold text-grey-8")

        for i in range(4):
            each_indicator_label = ui.label(f"[indicator {i + 1}] [accuracy]")

        user_name = app.storage.user.get("user_name", get_random_name())
        with ui.row() as row:
            label_welcome = ui.label(f"Welcome")
            label_name = ui.label(user_name)
        label_name.on("click", lambda: randomize_name(label_name))

        button_start = ui.button("SPOT THE BOT", on_click=lambda: start_game(label_name.text))

        create_footer()


def start_game(user_name: str) -> None:
    app.storage.user["user_name"] = user_name
    ui.open("/game")


@ui.page("/game")
def game_page() -> None:
    user_name = app.storage.user.get("user_name", None)
    if user_name is None:
        ui.open("/")
        return

    with ui.column() as column:
        text_context = ui.markdown("source information")
        text_content = ui.markdown("""Die ADF-RDA ist 1998 in der heutigen Form aus einer Fusion zwischen verschiedenen kleineren Parteien und der ADF mit dem 
    traditionsreichen Rassemblement Démocratique Africain, <span style="background-color: red;">RDA</span> hervorgegangen, in dessen programmatischer Tradition sie 
    sich bis heute sieht. Die ADF-RDA ist von der Wählerstärke her betrachtet eine der konstantesten Parteien Burkina Fasos. Bereits an den Parlamentswahlen vom 24. 
    Mai 1992 und 11. Mai 1997, welche von der ADF und dem RDA noch unabhängig voneinander bestritten wurden, kamen sie zusammen auf einen ähnlichen Wähleranteil von 
    rund 13 %.""")

        text_points = ui.markdown("10 points remaining")

        with ui.row() as row:
            text_paranoid = ui.markdown("paranoid")
            element_diagram = ui.element()
            text_gullible = ui.markdown("gullible")

        with ui.row() as row:
            button_bot = ui.button("BOT")
            button_human = ui.button("HUMAN")

    create_footer()


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


def main() -> None:
    ui.run(title="Spot the Bot", storage_secret="secret")


if __name__ in {"__main__", "__mp_main__"}:
    main()
