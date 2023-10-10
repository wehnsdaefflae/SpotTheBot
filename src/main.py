#!/usr/bin/env python3
import webbrowser
import uvicorn

from src.gui import frontend
from fastapi import FastAPI

app = FastAPI()
frontend.run(app)


def main() -> None:
    address = "0.0.0.0"
    port = 8000
    webbrowser.open(f"http://{address}:{port}")

    # `uvicorn main:app --reload --log-level debug --port 8000 --host 0.0.0.0`
    uvicorn.run("main:app", host=address, port=port, log_level="debug", reload=True)


if __name__ == '__main__':
    main()
