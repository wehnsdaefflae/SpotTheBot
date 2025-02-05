import datetime
import string
import tempfile

from loguru import logger
from nicegui import ui

from src.tools.misc import hex_color_segmentation


def int_to_base36(num: int) -> str:
    """
    Converts a positive integer to its base-36 string representation.
    Used for generating compact, URL-safe invitation links.
    
    Args:
        num (int): A positive integer to convert
        
    Returns:
        str: The base-36 string representation using digits 0-9 and lowercase letters a-z
        
    Examples:
        >>> int_to_base36(0)
        '0'
        >>> int_to_base36(42)
        '16'
        >>> int_to_base36(123456)
        '2n9c'
    """

    num = abs(num)
    if num == 0:
        return '0'

    symbols = string.digits + string.ascii_lowercase
    len_symbols = len(symbols)
    result = ""

    while 0 < num:
        remainder = num % len_symbols
        result = symbols[remainder] + result
        num //= len_symbols

    return result


def colorize(signs_dict: dict[str, float]) -> tuple[tuple[str, str], ...]:
    color_generator = hex_color_segmentation(.75)
    signs = sorted(signs_dict, key=signs_dict.get, reverse=True)
    return tuple((each_sign, next(color_generator)) for each_sign in signs)


def download_vcard(secret_name: str, public_name: str, face_id: str) -> tuple[str, str]:
    ram_disk_path = "/dev/shm/"
    now = datetime.datetime.now()
    photo_url = f"https://spotthebot.app/assets/images/portraits/{face_id}-2.jpg"
    on_mobile = True
    if on_mobile:
        with tempfile.NamedTemporaryFile(dir=ram_disk_path, mode="w", suffix=".vcf", delete=False) as file:
            file.write(f"BEGIN:VCARD\n")
            file.write(f"VERSION:3.0\n")
            file.write(f"N:{secret_name}\n")
            file.write(f"FN:{secret_name}\n")
            file.write(f"NICKNAME:{public_name}\n")
            file.write(f"PHOTO:{photo_url}\n")
            file.write(f"ORG:Spot The Bot\n")
            file.write(f"ROLE:Super Hero Private Detective\n")
            file.write(f"REV:{now.strftime('%Y%m%dT%H%M%SZ')}\n")
            file.write(f"URL:https://spotthebot.app\n")
            file.write(f"END:VCARD\n")

        return file.name, "spotthebot_secret_identity.vcf"

    with tempfile.NamedTemporaryFile(dir=ram_disk_path, mode="w", suffix=".txt", delete=False) as file:
        file.write(f"Secret identity for spotthebot.app: {secret_name}\n")

    return file.name, "spotthebot_secret_identity.txt"


def serve_id_file(secret_name: str) -> tuple[str, str]:
    ram_disk_path = "/dev/shm/"

    with tempfile.NamedTemporaryFile(dir=ram_disk_path, mode="w", suffix=".txt", delete=False) as file:
        file.write(
            f"Secret ID for spotthebot.app:\n"
            f"{secret_name}\n"
        )

    return file.name, "spotthebot_secret_identity.txt"


def remove_from_local_storage(key: str) -> None:
    try:
        command = f"localStorage.removeItem('{key}')"
        _ = ui.run_javascript(command)

    except TimeoutError as e:
        logger.error(e)


async def get_from_local_storage(key: str) -> str | None:
    try:
        command = f"localStorage.getItem('{key}')"
        _result = ui.run_javascript(command)
        result = await _result

    except TimeoutError as e:
        logger.error(e)
        result = None

    return result


def set_in_local_storage(key: str, value: str) -> None:
    try:
        command = f"localStorage.setItem('{key}', '{value}')"
        _ = ui.run_javascript(command)
        logger.info(f"Set '{key}' to '{value}'.")

    except TimeoutError as e:
        logger.error(e)


def make_xml(name: str, content: str | None = None, void_element: bool = False, **attributes: str) -> str:
    if void_element and content is not None:
        raise ValueError("Void elements cannot have content.")

    attributes = " ".join(f'{key.removesuffix("_")}="{value}"' for key, value in attributes.items())
    if void_element:
        return f"<{name} {attributes}/>"

    if content is None:
        return f"<{name} {attributes}></{name}>"

    return f"<{name} {attributes}>{content}</{name}>"
