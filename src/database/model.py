import json

from src.database.marker import Markers
from src.database.snippet import Snippets
from src.database.user import Users


class Model:
    def __init__(self, redis_config: dict[str, any]) -> None:
        users_db_config = redis_config.pop("users_database")
        snippets_db_config = redis_config.pop("snippets_database")
        markers_db_config = redis_config.pop("markers_database")

        self.users = Users(users_db_config)
        self.snippets = Snippets(snippets_db_config)
        self.markers = Markers(markers_db_config)
