# controller.py
from model import Model
from view import View


class Controller:
    def __init__(self):
        # Initialize Model with callback
        self.model = Model(self.model_callback)

        # Initialize View with callback
        self.view = View(self.view_callback)

    def model_callback(self, msg):
        print(f"Model Callback: {msg}")
        self.view.display_data(msg)

    def view_callback(self, msg):
        print(f"View Callback: {msg}")
        self.model.process_data(msg)
