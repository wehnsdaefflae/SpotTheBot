#!/usr/bin/env python3
import home_page
import theme

from nicegui import ui


# here we use our custom page decorator directly and just put the content creation into a separate function
@ui.page("/")
def index_page() -> None:
    with theme.frame("Homepage"):
        home_page.content()


@ui.page("/a")
def example_page_a() -> None:
    with theme.frame("- Example A -"):
        ui.label("Example A").classes("text-h4 text-grey-8")


@ui.page("/b")
def example_page_b() -> None:
    with theme.frame("- Example B -", logged_in="John Doe"):
        ui.label("Example B").classes("text-h4 text-grey-8")


@ui.page("/c")
def example_page() -> None:
    with theme.frame("- Example C -"):
        ui.label("Example C").classes("text-h4 text-grey-8")
        for i in range(1, 4):
            ui.link(f"Item {i}", f"/c/items/{i}").classes("text-xl text-grey-8")


@ui.page("/c/items/{id}", dark=True)
def item(id: str) -> None:
    with theme.frame(f"- Example C{id} -"):
        ui.label(f"Item  #{id}").classes("text-h4 text-grey-8")
        ui.link("go back", "/c").classes('text-xl text-grey-8')


def main() -> None:
    # we can also use the APIRouter as described in https://nicegui.io/documentation/page#modularize_with_apirouter
    # app.include_router(router)

    ui.run(title="Modularization Example")


if __name__ in {"__main__", "__mp_main__"}:
    main()
