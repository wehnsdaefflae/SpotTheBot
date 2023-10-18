from nicegui import ui, Client

from src.dataobjects import ViewCallbacks
from src.gui.elements.content_class import ContentPage


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


class DummyContent(ContentPage):
    def __init__(self, client: Client, callbacks: ViewCallbacks) -> None:
        super().__init__(client, callbacks)

    async def create_content(self) -> None:
        ui.label("Dummy content")
