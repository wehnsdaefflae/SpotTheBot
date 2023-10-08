import redislite


def initialize_counters(r: redislite.Redis):
    if not r.exists("user_id_counter"):
        r.set("user_id_counter", 0)

    if not r.exists("snippet_id_counter"):
        r.set("snippet_id_counter", 0)


def main() -> None:
    # todo:
    #  - [x] set key expiration
    #   - [x] put all relevant info in key value
    #   - [x] determine fast method to check all values
    # - [ ] do it for markers

    redis = redislite.Redis("spotthebot.rdb", db=0)

    initialize_counters(redis)


if __name__ == '__main__':
    main()
