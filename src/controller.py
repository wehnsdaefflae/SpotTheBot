from src.database.model import Model
from src.gui.page_main import View


class Controller:

    def __init__(self):
        self.model = Model()
        self.view = View()

        self.view.set_get_user(self.model.users.get_user)

