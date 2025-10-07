#!/usr/bin/env python3
import os
import sys

from nicegui import ui
from dotenv import load_dotenv

from src.controller import Controller

from loguru import logger

logger.add(sys.stderr, format="{time} {level} {message}", colorize=True, level="INFO")
logger.add("logs/file_{time}.log", backtrace=True, diagnose=True, rotation="500 MB", level="DEBUG")

load_dotenv()


def main() -> None:
    config = {
        "nicegui": {
            "host": os.environ.get("NICEGUI_HOST", "0.0.0.0"),
            "port": int(os.environ.get("NICEGUI_PORT", 8000)),
            "title": os.environ.get("NICEGUI_TITLE", "Spot The Bot!"),
            "uvicorn_logging_level": os.environ.get("UVICORN_LOGGING_LEVEL", "debug"),
            "storage_secret": os.environ.get("STORAGE_SECRET"),
            "reload": os.environ.get("RELOAD", "true").lower() == "true",
            "tailwind": os.environ.get("TAILWIND", "true").lower() == "true",
            "prod_js": os.environ.get("PROD_JS", "false").lower() == "true",
        },
        "openai": {
            "key": os.environ.get("OPENAI_API_KEY"),
            "parameters": {
                "model": os.environ.get("OPENAI_MODEL", "gpt-4-1106-preview"),
                "temperature": float(os.environ.get("OPENAI_TEMPERATURE", 0)),
                "top_p": os.environ.get("OPENAI_TOP_P"),
            },
        },
        "redis": {
            "users_database": {
                "host": os.environ.get("REDIS_HOST", "localhost"),
                "port": int(os.environ.get("REDIS_PORT", 6379)),
                "password": os.environ.get("REDIS_PASSWORD"),
                "db": 0,
            },
            "snippets_database": {
                "host": os.environ.get("REDIS_HOST", "localhost"),
                "port": int(os.environ.get("REDIS_PORT", 6379)),
                "password": os.environ.get("REDIS_PASSWORD"),
                "db": 1,
            },
            "markers_database": {
                "host": os.environ.get("REDIS_HOST", "localhost"),
                "port": int(os.environ.get("REDIS_PORT", 6379)),
                "password": os.environ.get("REDIS_PASSWORD"),
                "db": 2,
            },
            "invitations_database": {
                "host": os.environ.get("REDIS_HOST", "localhost"),
                "port": int(os.environ.get("REDIS_PORT", 6379)),
                "password": os.environ.get("REDIS_PASSWORD"),
                "db": 3,
            },
        },
    }

    nicegui_config = config.pop("nicegui")

    c = Controller(config)

    ui.run(**nicegui_config)


if __name__ in {"__main__", "__mp_main__"}:
    main()
