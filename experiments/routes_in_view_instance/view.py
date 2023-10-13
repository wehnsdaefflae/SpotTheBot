# view.py
from nicegui import ui


class View:
    def __init__(self):
        self.create_routes()

    def create_routes(self) -> None:
        @ui.page("/")
        def main_page() -> None:
            ui.label("Hello World!")
