from contextlib import contextmanager
from typing import Generator

from menu import menu

from nicegui import ui


@contextmanager
def frame(navtitle: str, logged_in: str | None = None) -> Generator[None, None, None]:
    """Custom page frame to share the same styling and behavior across all pages"""
    ui.colors(primary='#6E93D6', secondary='#53B689', accent='#111B1E', positive='#53B689')
    with ui.header().classes('justify-between text-white'):
        ui.label(navtitle)
        with ui.row():
            menu()

        if logged_in:
            link = ui.link(f'Log out {logged_in}', '/').classes('text-white')
            link.on('click', lambda: print('Logged out'))

    with ui.column().classes('absolute-center items-center'):
        yield
