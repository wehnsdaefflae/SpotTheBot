# coding=utf-8
from nicegui import app, ui, APIRouter

router = APIRouter(prefix="/c")



def main() -> None:
    app.include_router(router)
    ui.run(title="Spot the Bot")


if __name__ in {"__main__", "__mp_main__"}:
    main()
