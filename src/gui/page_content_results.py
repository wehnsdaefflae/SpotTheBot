import random

from loguru import logger
from nicegui import ui

from src.dataobjects import ViewStorage
from src.gui.elements.frame import create_footer


def results_content(view_storage: ViewStorage) -> None:
    logger.info("Results page")

    with ui.header(elevated=True):
        link_home = ui.link("home", "/")
        label_title = ui.label("Results")
    for i in range(10):
        ui.label(f"[result {i + 1}] [accuracy]")
    content = (
        f"TEXT {random.randint(0, 100)}:\n"
        f"\n"
        f"Die ADF-RDA ist 1998 in der heutigen Form aus einer Fusion zwischen verschiedenen kleineren Parteien und der ADF mit dem traditionsreichen Rassemblement "
        f"Démocratique Africain, RDA hervorgegangen, in dessen programmatischer Tradition sie sich bis heute sieht. Die ADF-RDA ist von der Wählerstärke her betrachtet "
        f"eine der konstantesten Parteien Burkina Fasos. Bereits an den Parlamentswahlen vom 24. Mai 1992 und 11. Mai 1997, welche von der ADF und dem RDA noch "
        f"unabhängig voneinander bestritten wurden, kamen sie zusammen auf einen ähnlichen Wähleranteil von rund 13 %."
    )
    text_example = ui.markdown(content)
    create_footer(view_storage)
