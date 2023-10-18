from nicegui import ui


async def persistent_dialog(message: str) -> ui.dialog:
    with ui.dialog().props("persistent") as dialog, ui.card():
        ui.label(message)
        ui.button("dismiss", on_click=lambda: dialog.submit("close"))

    await dialog

    return dialog
