#!/usr/bin/env python3
import json

from nicegui import ui

from src.controller import Controller


def main() -> None:
    c = Controller()

    with open("../config.json", mode="r") as config_file:
        config = json.load(config_file)

    nicegui_config = config["nicegui"]

    ui.run(**nicegui_config)


if __name__ in {"__main__", "__mp_main__"}:
    main()
