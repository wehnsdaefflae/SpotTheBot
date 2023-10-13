#!/usr/bin/env python3
import uvicorn

import example_pages

from nicegui import ui, app


def main() -> None:
    print(f"running main app {app.title}")
    # this call shows that you can also move the whole page creation into a separate file
    routes = example_pages.Routes()
    routes.setup_routes()

    ui.run(title="MWE", storage_secret="secret")
    uvicorn.run("main:app", host="0.0.0.0", port=8000)


if __name__ in {"__main__", "__mp_main__"}:
    main()
