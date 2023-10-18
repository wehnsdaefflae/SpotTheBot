from nicegui import ui

from src.dataobjects import Face


def show_face(face_seed: Face) -> ui.element:
    face_label = ui.label(str(face_seed))
    return face_label
