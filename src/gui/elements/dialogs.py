from nicegui import ui


async def info_dialog(message: str) -> str:
    with ui.dialog().props("persistent") as dialog, ui.card():
        ui.label(message)
        ui.button("Dismiss", on_click=lambda: dialog.submit("close"))

    return await dialog


async def input_dialog(message: str) -> str:
    with ui.dialog().props("persistent") as dialog, ui.card():
        ui.label(message)
        input_field = ui.input()

        def _submit_dialog() -> None:
            text = input_field.value
            if 0 < len(text):
                dialog.submit(text)

        input_field.on("change", _submit_dialog)

    return await dialog


async def result_dialog(message: str) -> str:
    with ui.dialog().props("persistent") as dialog, ui.card():
        ui.label(message)
        with ui.row():
            ui.button("Continue", on_click=lambda: dialog.submit("continue"))
            ui.button("quit", on_click=lambda: dialog.submit("quit"))

    return await dialog
