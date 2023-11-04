import redislite

from src.database.marker import MarkerManager
from src.database.snippet import Snippets
from src.database.user import Users


def main() -> None:
    # todo:
    #  - [x] set key expiration
    #   - [x] put all relevant info in key value
    #   - [x] determine fast method to check all values
    # - [x] do it for markers
    # - [ ] test each class

    user_interface = redislite.Redis("../database/spotthebot.rdb", db=0)
    snippet_interface = redislite.Redis("../database/spotthebot.rdb", db=1)
    marker_interface = redislite.Redis("../database/spotthebot.rdb", db=2)

    user_db = Users(user_interface)
    snippet_db = Snippets(snippet_interface)
    marker_db = MarkerManager(marker_interface)


if __name__ == '__main__':
    main()
