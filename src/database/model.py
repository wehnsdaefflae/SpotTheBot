import json

from src.database.marker import Markers
from src.database.snippet import Snippets
from src.database.user import Users


class Model:
    def __init__(self):
        with open("../config.json", mode="r") as config_file:
            self.config = json.load(config_file)

        redis_config = self.config["redis"]

        users_db_config = redis_config["users_database"]
        snippets_db_config = redis_config["snippets_database"]
        markers_db_config = redis_config["markers_database"]

        self.users = Users(users_db_config)
        self.snippets = Snippets(snippets_db_config)
        self.markers = Markers(markers_db_config)
