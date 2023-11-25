import os


def consolidate() -> None:
    all_faces = list()

    for each_file in os.listdir("faces"):
        if not each_file.endswith(".txt"):
            continue

        with open(f"faces/{each_file}", mode="r") as f:
            file_contents = f.read()

        all_faces.append(file_contents.strip())

    with open("all_faces.txt", mode="w") as f:
        f.write("\n".join(all_faces))


age_distribution = {
    "0-4 years": "toddler",
    "5-9 years": "child",
    "10-14 years": "preteen",
    "15-19 years": "teenager",
    "20-24 years": "young adult",
    "25-29 years": "adult",
    "30-34 years": "adult",
    "35-39 years": "adult",
    "40-44 years": "middle-aged person",
    "45-49 years": "middle-aged person",
    "50-54 years": "middle-aged person",
    "55-59 years": "middle-aged person",
    "60-64 years": "senior",
    "65-69 years": "senior",
    "70-74 years": "elderly person",
    "75-79 years": "elderly person",
    "80-84 years": "elderly person",
    "85+ years": "elderly person"
}


def rewrite_age() -> None:
    output_lines = list()

    with open("all_faces.txt", mode="r") as f:
        for each_line in f.readlines():
            for each_range, each_term in age_distribution.items():
                each_line = each_line.replace(f"{each_range} years old", each_term)
            output_lines.append(each_line.strip())

    with open("all_faces_new.txt", mode="w") as f:
        f.write("\n".join(output_lines))


def main() -> None:
    # consolidate()
    rewrite_age()


if __name__ == "__main__":
    main()
