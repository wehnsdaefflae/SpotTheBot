import redislite

from database.marker import Markers
from database.snippet import Snippets
from database.user import Users


def main() -> None:
    # todo:
    #  - [x] set key expiration
    #   - [x] put all relevant info in key value
    #   - [x] determine fast method to check all values
    # - [x] do it for markers
    # - [ ] test each class

    user_interface = redislite.Redis("spotthebot.rdb", db=0)
    snippet_interface = redislite.Redis("spotthebot.rdb", db=1)
    marker_interface = redislite.Redis("spotthebot.rdb", db=2)

    user_db = Users(user_interface)
    snippet_db = Snippets(snippet_interface)
    marker_db = Markers(marker_interface)


if __name__ == '__main__':
    main()
