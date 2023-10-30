from nicegui import app, ui

from controller import Controller


def main() -> None:
    print(f"running main app {app.title}")

    controller = Controller()
    controller.view.create_routes()

    ui.run(host="0.0.0.0", port=8000, title="MWE", storage_secret="secret")


if __name__ in {"__main__", "__mp_main__"}:
    main()

