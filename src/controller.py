from src.database.model import Model
from src.dataobjects import ViewCallbacks
from src.gui.view import View


class Controller:
    def __init__(self):
        self.model = Model()
        self.view = View()

        view_callbacks = ViewCallbacks(
            self.model.users.get_user,
            self.model.users.create_user,
        )

        self.view.set_callbacks(view_callbacks)
        self.view.setup_routes()
