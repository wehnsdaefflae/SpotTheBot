from nicegui import ui

from src.dataobjects import Face


def show_face(face: Face) -> ui.element:
    face_image = ui.image(f"assets/images/portraits/{face.source_id}-2.jpg")
    # face_label = ui.label(str(face_seed))
    return face_image
