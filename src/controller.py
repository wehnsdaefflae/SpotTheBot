from src.database.model import Model
from src.dataobjects import ViewCallbacks
from src.gui.view import View


class Controller:
    def __init__(self, config: dict[str, any]) -> None:
        config_databases = config.pop("redis")
        self.model = Model(config_databases)
        self.view = View()

        view_callbacks = ViewCallbacks(
            self.model.users.get_user,
            self.model.users.create_user,
            self.model.snippets.get_next_snippet,
            self.model.users.update_user_state,
            self.model.markers.update_markers,
        )

        self.view.set_callbacks(view_callbacks)
        self.view.setup_routes()
