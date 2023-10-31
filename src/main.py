#!/usr/bin/env python3
import webbrowser
from nicegui import ui

from src.controller import Controller


# redis-server database/redis.conf

def main() -> None:
    c = Controller()

    address = "0.0.0.0"
    port = 8000
    # webbrowser.open(f"http://{address}:{port}")

    ui.run(
        host=address, port=port,
        title="Spot The Bot!",
        uvicorn_logging_level="debug",
        storage_secret="secret",
        reload=True
    )


if __name__ in {"__main__", "__mp_main__"}:
    main()
