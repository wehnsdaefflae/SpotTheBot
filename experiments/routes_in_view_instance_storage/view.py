from nicegui import ui, app


class View:
    def __init__(self):
        self.d = {"text_input": "initial value"}

    def create_routes(self) -> None:
        # @ui.page("/")
        def main_page() -> None:
            label = ui.label()
            label.bind_text_from(self.d, "text_input")
            text_input = ui.input("tell me")
            text_input.on("change", lambda: self.d.__setitem__("text_input", text_input.value))

        @ui.page('/')
        def example_page_a():
            ui.label("Example works")
