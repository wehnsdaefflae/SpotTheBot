import json

from src.database.marker import Markers


def main() -> None:
    with open("../config.json", mode="r") as config_file:
        config = json.load(config_file)

    database_configs = config["redis"]
    markers_config = database_configs["markers_database"]

    marker_database = Markers(markers_config)

    marker: Marker


if __name__ == "__main__":
    main()
