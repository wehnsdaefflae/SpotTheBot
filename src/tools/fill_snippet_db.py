# coding=utf-8

import pathlib
from typing import Generator

import pandas

from src.database.snippet import Snippets, Snippet


def get_snippets(csv_file_path: pathlib.Path, snippet_id: list[int]) -> Generator[Snippet, None, None]:
    # get name of containing directory
    dir_name = csv_file_path.parent.name

    # get first name of file
    file_name = csv_file_path.name

    video_name = file_name.split("_")[1].removesuffix(".csv")

    csv_data = pandas.read_csv(csv_file_path.as_posix())
    for i, each_row in csv_data.iterrows():
        name = each_row["Name"]
        comment = each_row["Comment"]
        time_str = each_row["Time"]
        likes = each_row["Likes"]
        reply_count = each_row["Reply Count"]

        metadata_dict = {"likes": int(likes), "reply_count": int(reply_count), "time": time_str, "channel": dir_name, "video": video_name}
        metadata = tuple(tuple(each_item) for each_item in metadata_dict.items())
        yield Snippet(snippet_id[0], comment, f"Kommentar von '{name}' zum YouTube-Video '{video_name}' von {dir_name}", False, metadata)
        snippet_id[0] += 1


def main() -> None:
    snippet_database = Snippets()

    path = pathlib.Path("/home/mark/PycharmProjects/SpotTheBot/data/YouTube Deutschland")
    snippet_id = [0]

    for each_dir in sorted(path.iterdir()):
        if not each_dir.is_dir():
            continue

        for each_file in sorted(each_dir.iterdir(), key=lambda x: int(x.name.split("_")[0])):
            if not each_file.is_file():
                continue

            if not each_file.name.endswith(".csv"):
                continue

            print(each_file)
            snippets = set()
            likes = list()
            for each_snippet in get_snippets(each_file, snippet_id):
                snippet_database.set_snippet(each_snippet.text, each_snippet.source, each_snippet.is_bot, dict(each_snippet.metadata))

                each_likes = each_snippet.metadata[0][1]
                likes.append(each_likes)
                if each_likes < 10:
                    continue
                snippets.add(each_snippet)

            print(f"Added {len(snippets)} snippets.")
            continue


if __name__ == "__main__":
    main()
