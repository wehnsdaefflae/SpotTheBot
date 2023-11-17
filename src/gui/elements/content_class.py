from abc import ABC, abstractmethod

from nicegui import Client, ui

from src.dataobjects import ViewCallbacks


class ContentPage(ABC):
    def __init__(self, client: Client, callbacks: ViewCallbacks) -> None:
        self.client = client
        self.callbacks = callbacks

        main_container = ui.query("#c3")
        main_container.classes("items-center")
        # main_container.classes("justify-center")

    @abstractmethod
    async def create_content(self) -> None:
        raise NotImplementedError()
