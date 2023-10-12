from nicegui import ui


def create_footer() -> None:
    with ui.footer() as footer:
        with ui.row() as row:
            label_aces = ui.link("check out friends", "/friends")
            label_results = ui.link("check out results", "/results")
            label_about = ui.link("about", "/about")
