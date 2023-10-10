import random


def create_full_name(
        title: str | None,
        first_name_prefix: str, first_name_suffix: str | None,
        middle_name: str | None,
        surname_prefix: str, surname_suffix: str | None,
        suffix: str | None):
    """
    Combine provided name components into a full name.

    :param title: Honorific title (e.g., Mr., Mrs.)
    :param first_name_prefix: Prefix part of the given name
    :param first_name_suffix: Suffix part of the given name
    :param middle_name: Middle name(s) of the person
    :param surname_prefix: Prefix part of the surname
    :param surname_suffix: Suffix part of the surname
    :param suffix: Suffix (e.g., Jr., Sr., Ph.D.)

    :return: Full name as a string
    """

    # Using a list to gather name parts; this helps in managing spaces efficiently.
    name_parts = list()

    if title:
        name_parts.append(title)

    # Combining first name prefix and suffix.
    if first_name_prefix or first_name_suffix:
        name_parts.append(f"{first_name_prefix or ''}{first_name_suffix or ''}")

    if middle_name:
        name_parts.append(middle_name)

    # Combining surname prefix and suffix.
    if surname_prefix or surname_suffix:
        name_parts.append(f"{surname_prefix or ''}{surname_suffix or ''}")

    if suffix:
        name_parts.append(suffix)

    # Join the name parts with spaces and return.
    return ' '.join(name_parts)


def get_seed(dim: int) -> tuple[float, ...]:
    return tuple(random.random() for _ in range(dim))


def generate_name(seed: tuple[float, ...] | None = None) -> str:
    titles = [
        None,
        "Mr.", "Mrs.", "Miss", "Ms.", "Dr.",
        "Prof.", "Sir", "Dame", "Rev.", "Rabbi",
        "Imam", "Lord", "Lady", "Capt.",
        "Cpl.", "Maj.", "Col.", "Gen."
    ]
    # len = 19

    first_name_prefixes = [
        "John", "Mary", "Rob", "Pat", "Mich",
        "Eliza", "Chris", "Ben", "Steph", "Greg",
        "Nath", "Mel", "Fred", "Ed", "Phil",
        "Cath", "Mike", "Jess", "Sam", "Tim"
    ]
    # len = 20

    first_name_suffixes = [
        None,
        "son", "beth", "ert", "rick", "elle",
        "a", "ina", "lyn", "ie", "fer",
        "an", "thy", "ise", "ry", "dra",
        "ton", "vin", "dy", "lee", "nor"
    ]
    # len = 21

    middle_names = [
        None,
        "Lee", "Marie", "Ann", "Lynn", "Ray",
        "Jean", "May", "Rose", "Grace", "Joe",
        "Mae", "Jay", "Lou", "Roy", "Dawn",
        "Faye", "Kay", "Sky", "Eve", "Elle"
    ]
    # len = 21

    surname_prefixes = [
        "Goldman", "Silverstein", "Greenwood", "Blackwood", "Whitman",
        "Redford", "Bluestone", "VanBuren", "O'Connell", "McCarthy",
        "Browning", "Winters", "Summers", "Springs", "Autumn",
        "Eastwood", "Westbrook", "Northman", "Southgate", "Woodward"
    ]
    # len = 20

    surname_suffixes = [
        None,
        "smith", "ton", "field", "berg", "stone",
        "wood", "land", "man", "ford", "wick",
        "shire", "brook", "dale", "son", "worth",
        "lake", "hill", "well", "bottom", "ridge"
    ]
    # len = 21

    suffixes = [
        None,
        "Jr.", "Sr.", "II", "V", "VI", "VII", "VIII", "IX",
        "X", "Ph.D.", "M.D.", "Esq.", "B.A.",
        "M.A.", "LL.B.", "of Darkmoor", "of Sunvalley",
        "of Moonshadow", "of Starfall", "of Windyridge",
        "of Thundercliff", "of Rainhaven",
    ]
    # len = 23

    if seed is None:
        title = random.choice(titles)
        first_name_prefix = random.choice(first_name_prefixes)
        first_name_suffix = random.choice(first_name_suffixes)
        middle_name = random.choice(middle_names)
        surname_prefix = random.choice(surname_prefixes)
        surname_suffix = random.choice(surname_suffixes)
        suffix = random.choice(suffixes)
    else:
        title = titles[int(seed[0] * len(titles))]
        first_name_prefix = first_name_prefixes[int(seed[1] * len(first_name_prefixes))]
        first_name_suffix = first_name_suffixes[int(seed[2] * len(first_name_suffixes))]
        middle_name = middle_names[int(seed[3] * len(middle_names))]
        surname_prefix = surname_prefixes[int(seed[4] * len(surname_prefixes))]
        surname_suffix = surname_suffixes[int(seed[5] * len(surname_suffixes))]
        suffix = suffixes[int(seed[6] * len(suffixes))]

    full_name = create_full_name(
        title,
        first_name_prefix,
        first_name_suffix,
        middle_name,
        surname_prefix,
        surname_suffix,
        suffix
    )

    return full_name
