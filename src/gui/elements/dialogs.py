from nicegui import ui


async def info_dialog(message_txt: str) -> str:
    with ui.dialog().props("persistent") as dialog, ui.card():
        with ui.markdown(message_txt) as message:
            message.classes("w-full text-lg ")

        with ui.button("Alles klar!", on_click=lambda: dialog.submit("close")) as button:
            button.classes("w-full ")

    return await dialog


async def option_dialog(message: str, options: list[str]) -> str:
    with ui.dialog().props("persistent") as dialog, ui.card():
        ui.label(message)
        with ui.row() as row:
            row.classes("flex justify-evenly w-full ")
            for each_option in options:
                ui.button(each_option, on_click=lambda _option=each_option: dialog.submit(_option))

    return await dialog


async def input_dialog(message_text: str) -> str:
    with ui.dialog().props("persistent") as dialog, ui.card():
        with ui.label(message_text) as message:
            message.classes("w-full text-lg ")

        with ui.input() as input_field:
            input_field.classes("w-full text-lg ")

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
