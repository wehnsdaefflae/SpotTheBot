from nicegui import ui, app

from controller import Controller
import uvicorn


def main() -> None:
    print(f"running main app {app.title}")

    controller = Controller()

    ui.run(title="MWE", storage_secret="secret")
    uvicorn.run("main:app", host="0.0.0.0", port=8000)


if __name__ in {"__main__", "__mp_main__"}:
    main()
