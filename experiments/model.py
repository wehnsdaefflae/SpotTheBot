class Model:
    def __init__(self, callback_from_view=None):
        self.callback_from_view = callback_from_view

    def process_data(self, data):
        print(f"Processing data: {data}")
        if self.callback_from_view:
            self.callback_from_view(f"Processed {data}")