# coding=utf-8
import json
import pathlib
from typing import Generator

import pandas
import bs4

from src.database.snippet import Snippets, Snippet


def get_snippets(csv_file_path: pathlib.Path) -> Generator[Snippet, None, None]:
    # get name of containing directory
    dir_name = csv_file_path.parent.name

    # get first name of file
    file_name = csv_file_path.name

    video_name = file_name.split("_")[1].removesuffix(".csv")

    csv_data = pandas.read_csv(csv_file_path.as_posix())
    for i, each_row in csv_data.iterrows():
        comment_raw = each_row["Comment"]
        if not isinstance(comment_raw, str):
            continue
        soup = bs4.BeautifulSoup(comment_raw, "html.parser")
        comment = soup.get_text().strip()

        name_raw = each_row["Name"]
        if not isinstance(name_raw, str):
            continue
        name = name_raw.strip()

        time_str_raw = each_row["Time"]
        if not isinstance(time_str_raw, str):
            continue
        time_str = time_str_raw.strip()

        likes = each_row["Likes"]
        reply_count = each_row["Reply Count"]

        metadata_dict = {
            "likes": int(likes),
            "reply_count": int(reply_count),
            "time": time_str,
            "channel": dir_name,
            "video": video_name
        }
        metadata = tuple(tuple(each_item) for each_item in metadata_dict.items())

        yield Snippet(
            comment,
            f"Kommentar von '{name}' zum YouTube-Video '{video_name}' von {dir_name}",
            False, metadata)


def main() -> None:
    with open("../config.json", mode="r") as config_file:
        config = json.load(config_file)

    database_configs = config["redis"]
    snippets_config = database_configs["snippets_database"]

    snippet_database = Snippets(snippets_config)

    path = pathlib.Path("/home/mark/Downloads/kaggle/archive (11)/YouTube Deutschland")
    snippets_added = 0

    for each_dir in sorted(path.iterdir()):
        if not each_dir.is_dir():
            continue

        for each_file in sorted(each_dir.iterdir(), key=lambda x: int(x.name.split("_")[0])):
            if not each_file.is_file():
                continue

            if not each_file.name.endswith(".csv"):
                continue

            print(each_file)
            for each_snippet in get_snippets(each_file):
                each_likes = each_snippet.metadata[0][1]
                if each_likes < 10 or len(each_snippet.text) < 250:
                    continue

                snippet_database.set_snippet(
                    each_snippet.text,
                    each_snippet.source,
                    each_snippet.is_bot,
                    dict(each_snippet.metadata)
                )
                snippets_added += 1

    print(f"Added {snippets_added} snippets.")


if __name__ == "__main__":
    # redis-server database/redis.conf
    main()
