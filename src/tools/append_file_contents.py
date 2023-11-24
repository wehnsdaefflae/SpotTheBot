import os


def main() -> None:
    all_faces = list()

    for each_file in os.listdir("faces"):
        if not each_file.endswith(".txt"):
            continue

        with open(f"faces/{each_file}", mode="r") as f:
            file_contents = f.read()

        all_faces.append(file_contents.strip())

    with open("all_faces.txt", mode="w") as f:
        f.write("\n".join(all_faces))


if __name__ == "__main__":
    main()
