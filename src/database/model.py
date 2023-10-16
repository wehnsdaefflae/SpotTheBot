from src.database.marker import Markers
from src.database.snippet import Snippets
from src.database.user import Users


class Model:
    def __init__(self):
        self.users = Users(debugging=False)
        self.snippets = Snippets(debugging=False)
        self.markers = Markers(debugging=False)
