import os
import pathlib
from typing import Generator

from src.database.snippet import Snippet


def get_snippets(csv_file_path: str, snippet_id: list[int]) -> Generator[Snippet, None, None]:
    # get name of containing directory
    dir_name = pathlib.Path(csv_file_path).parent.name

    # get first name of file
    file_name = pathlib.Path(csv_file_path).name

    with open(csv_file_path, mode="r") as csv_file:
        next(csv_file)  # Skip header

        for each_line in csv_file:
            each_line_stripped = each_line.strip()
            comma_separated = each_line_stripped.split(",")
            name = comma_separated[0]
            time_str, likes, reply_count = comma_separated[-3:]

            comment_prefix = f"{name},"
            comment_suffix = f",{time_str},{likes},{reply_count}"
            comment = each_line_stripped.removeprefix(comment_prefix).removesuffix(comment_suffix)
            comment = comment.removeprefix('"').removesuffix('"')

            # time = datetime.strptime(time_str, '%Y-%m-%dT%H:%M:%SZ')

            metadata_dict = {"likes": likes, "reply_count": reply_count, "time": time_str, "channel": dir_name, "video": file_name}
            metadata = tuple(tuple(each_item) for each_item in metadata_dict.items())
            yield Snippet(snippet_id[0], comment, f"YouTube-Kommentar", False, metadata)
            snippet_id[0] += 1


def main() -> None:
    path = "/home/mark/bananapi/home/mark/320GBNAS/kaggle/archive (11)/YouTube Deutschland/Dinge Erklärt - Kurzgesagt/"
    snippet_id = [0]

    for each_file in sorted(os.listdir(path), key=lambda x: int(x.split("_")[0])):
        if not each_file.endswith(".csv"):
            continue

        print(each_file)
        snippets = set()
        likes = list()
        for each_snippet in get_snippets(path + each_file, snippet_id):
            snippets.add(each_snippet)
            likes.append(each_snippet.metadata[0][1])

        continue


if __name__ == "__main__":
    main()
