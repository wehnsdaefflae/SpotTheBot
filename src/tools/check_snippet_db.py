import redislite

from src.database.snippet import Snippets


def main() -> None:
    snippet_database = Snippets(redis=redislite.Redis("../../database/spotthebot.rdb", db=1))
    i = 0
    while True:
        try:
            snippet = snippet_database.get_snippet(i)
            if i % 1_000 == 0:
                print(snippet)
        except KeyError:
            print(f"Snippet {i} does not exist.")
            break
        i += 1


if __name__ == "__main__":
    main()
