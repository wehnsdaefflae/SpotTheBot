# view.py
from fastapi import FastAPI

app = FastAPI()


class View:
    def __init__(self, callback_from_model=None):
        self.callback_from_model = callback_from_model

    def display_data(self, data):
        print(f"Displaying data: {data}")
        if self.callback_from_model:
            self.callback_from_model(f"Displayed {data}")


@app.get("/")
def read_root():
    # For the sake of the demonstration, this route isn't interacting with the View instance.
    # You can adjust this to call methods on the View if needed.
    return {"Hello": "World"}
