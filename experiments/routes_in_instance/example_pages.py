from nicegui import ui


class Routes:
    def __init__(self):
        self.time = 0

    def setup_routes(self) -> None:
        @ui.page('/')
        def example_page_a():
            ui.label("Example works")
