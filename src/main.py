#!/usr/bin/env python3
import webbrowser
import uvicorn

from src.controller import Controller


def main() -> None:
    c = Controller()

    address = "0.0.0.0"
    port = 8000
    # webbrowser.open(f"http://{address}:{port}")

    # `uvicorn main:app --reload --log-level debug --port 8000 --host 0.0.0.0`
    # uvicorn.run("main:app", host=address, port=port, log_level="debug", reload=True)
    uvicorn.run("gui.page_main:main_app", host=address, port=port, log_level="debug")


if __name__ in {"__main__", "__mp_main__"}:
    main()
