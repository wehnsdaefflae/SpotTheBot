from src.database.model import Model
from src.gui.page_main import get_view_instance


class Controller:

    def __init__(self):
        self.model = Model()
        self.view = get_view_instance()

        self.view.set_get_user(self.model.users.get_user)

