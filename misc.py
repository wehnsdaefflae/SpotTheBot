#!/usr/bin/env python3
import itertools
from typing import Generator


POINT = tuple[float, ...]
CUBE = tuple[POINT, POINT]


def _divide(corners: CUBE, center: POINT) -> tuple[CUBE, ...]:
    return tuple((_x, center) for _x in itertools.product(*zip(*corners)))


def _center(corners: CUBE) -> POINT:
    point_a, point_b = corners
    return tuple((_a + _b) / 2. for _a, _b in zip(point_a, point_b))


def uniform_segmentation(dimensionality: int) -> Generator[tuple[CUBE, POINT], None, None]:
    corners = tuple(0. for _ in range(dimensionality)), tuple(1. for _ in range(dimensionality))
    spaces = [corners]

    while True:
        _spaces_new = []
        while 0 < len(spaces):
            _each_cube = spaces.pop()
            center = _center(_each_cube)
            _segments = _divide(_each_cube, center)
            _spaces_new.extend(_segments)
            yield _each_cube, center

        spaces = _spaces_new


def hex_color_segmentation(lightness: float) -> Generator[str, None, None]:
    dimensions = 2
    generator_segmentation = uniform_segmentation(dimensions)

    while True:
        _, (hue, saturation) = next(generator_segmentation)
        yield f"hsl({int(hue * 360)}, {int(saturation * 100)}%, {int(lightness * 100)}%)"


def main():
    generator_segmentation = hex_color_segmentation()

    while True:
        color = next(generator_segmentation)
        print(color)


if __name__ == "__main__":
    main()
