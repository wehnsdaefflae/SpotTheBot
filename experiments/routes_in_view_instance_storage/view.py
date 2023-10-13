from nicegui import ui, app


class View:
    def __init__(self):
        self.create_routes()

    def create_routes(self) -> None:
        @ui.page("/")
        def main_page() -> None:
            name = app.storage.user.get("name", "default")
            ui.label(f"Hello {name}!")
