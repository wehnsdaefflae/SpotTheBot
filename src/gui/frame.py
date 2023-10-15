from nicegui import ui, app


async def logout() -> None:
    with ui.dialog().props("persistent") as dialog, ui.card():
        ui.label("Are you sure you want to log out?")
        with ui.row() as button_row:
            ui.button("yes", on_click=lambda: dialog.submit("yes"))
            ui.button("no", on_click=lambda: dialog.submit("no"))

    result = await dialog
    if result == "yes":
        app.storage.user.pop("name_hash", None)
        app.storage.user.pop("identity_file", None)

        ui.open("/")


def create_footer() -> None:
    with ui.footer() as footer:
        with ui.row() as row:
            label_aces = ui.link("check out friends", "/friends")
            label_results = ui.link("check out results", "/results")
            label_about = ui.link("about", "/about")

            label_logout = ui.label("[logout]")
            label_logout.classes("cursor-pointer")
            label_logout.on("click", logout)

