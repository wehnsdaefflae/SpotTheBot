from src.database.marker_manager import MarkerManager
from src.database.snippet_manager import SnippetManager
from src.database.user_manager import UserManager


class Model:
    def __init__(self, redis_config: dict[str, any]) -> None:
        users_db_config = redis_config.pop("users_database")
        snippets_db_config = redis_config.pop("snippets_database")
        markers_db_config = redis_config.pop("markers_database")

        self.users = UserManager(users_db_config)
        self.snippets = SnippetManager(snippets_db_config)
        self.markers = MarkerManager(markers_db_config, max_markers=100)
