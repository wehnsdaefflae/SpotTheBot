import os
from typing import List


def get_files_in_directory(directory: str) -> list[str]:
    """Get a list of file names in the given directory."""
    return [f for f in os.listdir(directory) if os.path.isfile(os.path.join(directory, f))]


def rename_files_consecutively(directory: str) -> None:
    """Rename all files in the specified directory with consecutive numbers."""
    files = get_files_in_directory(directory)
    files.sort()  # Sort files alphabetically before renaming

    for index, filename in enumerate(files, start=1):
        file_extension = os.path.splitext(filename)[1]
        new_filename = f"{index:04}{file_extension}"  # Format: 0001.jpg, 0002.png, etc.
        os.rename(os.path.join(directory, filename), os.path.join(directory, new_filename))


if __name__ == "__main__":
    directory_path = "/home/mark/banana_pi/sync/project_data/Prototype_botornot/project_files/base_faces/03_mouths/"
    rename_files_consecutively(directory_path)
