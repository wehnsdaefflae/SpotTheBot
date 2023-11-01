#!/usr/bin/env python3
import json

from nicegui import ui, app, Client


def js_log(text: str) -> None:
    print(text)
    js = f"console.log({json.dumps(text)});"
    _ = ui.run_javascript(js)


def init_js() -> None:
    js = (
        "window.spotTheBot = {",
        "    count: 0,",
        "    increment: function() {",
        "        this.count++;",
        "        return this.count;",
        "    },",
        "    decrement: function() {",
        "        if (this.count > 0) {",
        "            this.count--;",
        "        }",
        "        return this.count;",
        "    }",
        "};",
    )

    _ = ui.run_javascript("\n".join(js))


async def increment() -> int:
    js = "spotTheBot.increment();"
    response = ui.run_javascript(js)
    result = await response
    print(result)
    return int(result)


async def decrement() -> int:
    js = "spotTheBot.decrement();"
    response = ui.run_javascript(js)
    result = await response
    print(result)
    return int(result)


@ui.page('/')
async def example_page_a(client: Client):
    await client.connected()

    init_js()
    js_log("initialized js")

    button_increment = ui.button("Increment", on_click=increment)
    button_decrement = ui.button("Decrement", on_click=decrement)


def main() -> None:
    print(f"running main app {app.title}")

    ui.run(title="MWE", storage_secret="secret")


if __name__ in {"__main__", "__mp_main__"}:
    main()
