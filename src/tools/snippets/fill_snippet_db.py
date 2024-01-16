# coding=utf-8
import asyncio
import dataclasses

import json
import math
import pathlib
import random
import re
import time
from typing import Generator

import pandas
import bs4

from src.database.snippet_manager import SnippetManager
from src.dataobjects import Snippet
from src.tools.snippets.generate_fake_comments import PromptOpenAI, get_fake_comments


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
            "video": video_name,
            "commentator": name
        }
        metadata = tuple(tuple(each_item) for each_item in metadata_dict.items())

        yield Snippet(
            comment,
            "https://www.kaggle.com/datasets/maxmnemo1010/germanyoutubecomments",
            False, metadata)


def snippets_from_file_system(
        path_str: str,
        min_likes: int = 5, min_text: int = 250, max_text: int = 1_000) -> Generator[Snippet, None, None]:

    path = pathlib.Path(path_str)

    for each_dir in sorted(path.iterdir()):
        if not each_dir.is_dir():
            continue

        for each_file in sorted(each_dir.iterdir(), key=lambda x: int(x.name.split("_")[0])):
            if not each_file.is_file():
                continue

            if not each_file.name.endswith(".csv"):
                continue

            for each_snippet in get_snippets(each_file):
                each_likes = each_snippet.metadata[0][1]
                len_text = len(each_snippet.text)
                if each_likes < min_likes or len_text < min_text or max_text < len_text:
                    continue

                yield each_snippet


def remove_all_fakes() -> None:
    def extract_index(key: str) -> int:
        match = re.search(r'snippet:(\d+)', key)
        if match:
            return int(match.group(1))

        return -1

    cursor = '0'
    while True:
        cursor, keys = redis.scan(cursor, match='snippet:*')
        for each_key in keys:
            index = extract_index(each_key)  # Implement this function to extract the index from the key
            if index >= 8884:
                redis.delete(each_key)
        if cursor == '0':
            break


async def main() -> None:
    with open("../../../config.json", mode="r") as config_file:
        config = json.load(config_file)

    database_configs = config["redis"]
    snippets_config = database_configs["snippets_database"]

    snippet_database = SnippetManager(snippets_config)

    """
    no_auth_comments = await add_authentic_comments(snippet_database)
    # 8884 added
    """
    no_auth_comments = 8884

    openai_config = config["openai"]
    prompt_openai = PromptOpenAI(openai_config)

    # todo: request in parallel

    iterations = int(math.ceil(no_auth_comments / 3))
    for i in range(iterations):
        print(f"Generating fake comments {i + 1} / {iterations}")
        await add_fake_comments(prompt_openai, snippet_database, no_auth_comments)


async def add_fake_comments(prompt_openai: PromptOpenAI, snippet_database: SnippetManager, auth_snippet_count: int) -> None:
    no_examples = 5
    example_snippets = tuple(
        snippet_database.get_snippet(random.randint(0, auth_snippet_count - 1))
        for _ in range(no_examples)
    )

    example_content = list()
    for each_snippet in example_snippets:
        d = dataclasses.asdict(each_snippet)
        d_str = json.dumps(d)
        example_content.append(d_str)

    while True:
        try:
            fake_comments = await get_fake_comments(prompt_openai, example_content, output_comments=3)
            generated_snippets = list()

            for each_fake_comment in fake_comments:
                json_dict = json.loads(each_fake_comment)
                json_dict["is_bot"] = True
                each_snippet = Snippet(**json_dict)
                generated_snippets.append(each_snippet)

            for each_snippet in generated_snippets:
                snippet_database.set_snippet(
                    each_snippet.text,
                    each_snippet.source,
                    True,
                    dict(each_snippet.metadata)
                )

            break

        except Exception as e:
            print(e)
            time.sleep(1)


async def add_authentic_comments(snippet_database: SnippetManager) -> int:
    path = "/home/mark/nas/data/kaggle/archive (11)/YouTube Deutschland"
    snippets_added = 0
    for each_snippet in snippets_from_file_system(path):
        snippet_database.set_snippet(
            each_snippet.text,
            each_snippet.source,
            each_snippet.is_bot,
            dict(each_snippet.metadata)
        )
        snippets_added += 1
    print(f"Added {snippets_added} snippets.")
    return snippets_added


if __name__ == "__main__":
    # redis-server database/redis.conf
    asyncio.run(main())
