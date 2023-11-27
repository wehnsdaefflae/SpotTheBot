import hashlib
import os
import random


def cantor_pairing_function(k1: int, k2: int) -> int:
    return int(.5 * (k1 + k2) * (k1 + k2 + 1) + k2)


def inverse_cantor_pairing_function(z: int) -> tuple[int, int]:
    w = int(((8 * z + 1) ** .5 - 1) / 2)
    t = (w * w + w) // 2
    y = z - t
    x = w - y
    return int(x), int(y)


def int_to_base62(num: int) -> str:
    characters = "0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"
    base62 = []
    while num:
        num, rem = divmod(num, 62)
        base62.append(characters[rem])
    return ''.join(reversed(base62))


def base62_to_int(base62: str) -> int:
    characters = "0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"
    num = 0
    for char in base62:
        num = num * 62 + characters.index(char)
    return num


def pair_to_alphanumeric(k1: int, k2: int) -> str:
    cantor_value = cantor_pairing_function(k1,  k2 * 3 + 571)
    return int_to_base62(cantor_value)


def alphanumeric_to_pair(alphanum: str) -> tuple[int, int]:
    cantor_value = base62_to_int(alphanum)
    value_a, value_b = inverse_cantor_pairing_function(cantor_value)
    return value_a, (value_b - 571) // 3


def random_names(no_names: int = 100, length_name: int = 10) -> set[str]:
    characters = "0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"

    names = set()
    while len(names) < no_names:
        each_name = "".join(random.choice(characters) for _ in range(length_name))
        names.add(each_name)

    return names


def number_to_hash(number: int) -> str:
    a = hashlib.shake_128()
    a.update(str(number).encode("utf-8"))
    digest = a.hexdigest(4)
    return digest[::-1]


def rename_files() -> None:
    folder = "../../assets/images/portraits/"
    file_list = sorted(os.listdir(folder))
    names = list(random_names(len(file_list)))

    previous_names = set()

    for i, each_file in enumerate(file_list):
        if not each_file.endswith(".jpg"):
            continue

        each_name, each_extension = os.path.splitext(each_file)
        # index, variant = tuple(int(x) for x in each_name.split("-"))
        prev_id, variant_str = each_name.split("-")
        previous_names.add(prev_id)

        variant = int(variant_str)
        hash_name = number_to_hash(len(previous_names) - 1)

        source_name = f"{folder}{each_name}{each_extension}"
        target_name = f"{folder}{hash_name}-{variant}{each_extension}"

        os.rename(source_name, target_name)
        # print(f"{source_name} -> {target_name}")


def test() -> None:
    # test_pairs = ((random.randint(0, 1000), random.randint(0, 4)) for _ in range(1_000))
    test_pairs = (
        (2346, 0),
        (2346, 1),
        (2346, 2),
        (2347, 0),
        (2347, 1),
        (2347, 2),
    )

    for each_pair in test_pairs:
        each_name = pair_to_alphanumeric(*each_pair)
        _pair = alphanumeric_to_pair(each_name)
        print(f"{each_pair} -> {each_name} -> {_pair}")
        assert _pair == each_pair, f"{each_pair} != {_pair}"


def main() -> None:
    # test()
    rename_files()


if __name__ == "__main__":
    main()
