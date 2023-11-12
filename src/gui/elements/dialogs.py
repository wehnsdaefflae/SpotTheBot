from nicegui import ui


async def info_dialog(message: str) -> str:
    with ui.dialog().props("persistent") as dialog, ui.card():
        ui.label(message)
        ui.button("Dismiss", on_click=lambda: dialog.submit("close"))

    return await dialog


async def result_dialog(message: str) -> str:
    with ui.dialog().props("persistent") as dialog, ui.card():
        ui.label(message)
        with ui.row():
            ui.button("Continue", on_click=lambda: dialog.submit("continue"))
            ui.button("quit", on_click=lambda: dialog.submit("quit"))

    return await dialog
