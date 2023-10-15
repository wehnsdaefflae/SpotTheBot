from src.database.marker import Markers
from src.database.snippet import Snippets
from src.database.user import Users


class Model:
    def __init__(self):
        self.users = Users()
        self.snippets = Snippets()
        self.markers = Markers()
