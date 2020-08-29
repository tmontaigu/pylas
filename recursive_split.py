import argparse
import sys
from typing import List
from typing import Optional

import numpy as np

import pylas
from pylas import LazBackend


def recursive_split(x_min, y_min, x_max, y_max, max_x_size, max_y_size):
    x_size = x_max - x_min
    y_size = y_max - y_min

    if x_size > max_x_size:
        left = recursive_split(x_min, y_min, x_min + (x_size // 2), y_max, max_x_size, max_y_size)
        right = recursive_split(x_min + (x_size // 2), y_min, x_max, y_max, max_x_size, max_y_size)
        return left + right
    elif y_size > max_y_size:
        up = recursive_split(x_min, y_min, x_max, y_min + (y_size // 2), max_x_size, max_y_size)
        down = recursive_split(x_min, y_min + (y_size // 2), x_max, y_max, max_x_size, max_y_size)
        return up + down
    else:
        return [(x_min, y_min, x_max, y_max)]


def tuple_size(string):
    try:
        return tuple(map(float, string.split("x")))
    except:
        raise argparse.ArgumentError("Size must be in the form of 50.0x65.14")


def main():
    parser = argparse.ArgumentParser("LAS recursive splitter", description="Splits a las file bounds recursively")
    parser.add_argument("input_file")
    parser.add_argument("output_dir")
    parser.add_argument("size", type=tuple_size, help="eg: 50x64.17")

    args = parser.parse_args()

    with pylas.open(sys.argv[1]) as file:
        sub_bounds = recursive_split(
            file.header.x_min,
            file.header.y_min,
            file.header.x_max,
            file.header.y_max,
            args.size[0],
            args.size[1]
        )

        writers: List[Optional[pylas.LasWriter]] = [None] * len(sub_bounds)
        try:
            for points in file.chunk_iterator(10 ** 6):
                print(f"{len(points) / file.header.point_count * 100}%")
                for i, (x_min, y_min, x_max, y_max) in enumerate(sub_bounds):
                    mask = (points.x >= x_min) & (points.x <= x_max) & (points.y >= y_min) & (points.y <= y_max)

                    if np.any(mask):
                        if writers[i] is None:
                            writers[i] = pylas.open(f"{sys.argv[2]}/output_{i}.laz",
                                                    mode='w',
                                                    laz_backends=[LazBackend.LazrsParallel],
                                                    header=file.header)
                        sub_points = points[mask]
                        writers[i].write(sub_points)
        finally:
            for writer in writers:
                if writer is not None:
                    writer.close()


if __name__ == '__main__':
    main()
