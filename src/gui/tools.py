import datetime
import tempfile

from loguru import logger
from nicegui import ui, client

from src.tools.misc import hex_color_segmentation


def colorize(signs_dict: dict[str, int]) -> tuple[tuple[str, str], ...]:
    color_generator = hex_color_segmentation(.75)
    signs = sorted(signs_dict, key=signs_dict.get, reverse=True)
    return tuple((each_sign, next(color_generator)) for each_sign in signs)


def download_vcard(secret_name: str) -> tuple[str, str]:
    ram_disk_path = "/dev/shm/"
    now = datetime.datetime.now()
    on_mobile = True
    if on_mobile:
        with tempfile.NamedTemporaryFile(dir=ram_disk_path, mode="w", suffix=".vcf", delete=False) as file:
            # with open("contact.vcf", mode="w") as file:
            file.write(f"BEGIN:VCARD\n")
            file.write(f"VERSION:3.0\n")
            file.write(f"N:{secret_name}\n")
            file.write(f"FN:{secret_name}\n")
            file.write(f"ORG:Spot The Bot\n")
            file.write(f"ROLE:Super Hero Private Detective\n")
            file.write(f"REV:{now.strftime('%Y%m%dT%H%M%SZ')}\n")
            file.write(f"URL:https://spotthebot.app\n")
            file.write(f"END:VCARD\n")

        return file.name, "spotthebot_secret_identity.vcf"

    with tempfile.NamedTemporaryFile(dir=ram_disk_path, mode="w", suffix=".txt", delete=False) as file:
        file.write(f"Secret identity for spotthebot.app: {secret_name}\n")

    return file.name, "spotthebot_secret_identity.txt"


async def remove_from_local_storage(key: str) -> None:
    try:
        command = f"localStorage.removeItem('{key}')"
        await ui.run_javascript(command, respond=False)

    except TimeoutError as e:
        logger.error(e)


async def get_from_local_storage(key: str) -> str | None:
    try:
        command = f"localStorage.getItem('{key}')"
        _result = await ui.run_javascript(command, respond=True)
        result = _result

    except TimeoutError as e:
        logger.error(e)
        result = None

    return result


async def set_in_local_storage(key: str, value: str) -> None:
    try:
        command = f"localStorage.setItem('{key}', '{value}')"
        await ui.run_javascript(command, respond=False)

    except TimeoutError as e:
        logger.error(e)
