import io
import math

import numpy as np
import pytest

import pylas
from pylas import LazBackend

# noinspection PyUnresolvedReferences
from pylastests.test_common import all_laz_path, las_path_fixture


@pytest.fixture(params=LazBackend.detect_available())
def laz_backend(request):
    return request.param


def check_chunked_reading_is_gives_expected_points(groundtruth_las, reader, iter_size):
    """Checks that the points read by the reader are the same as groundtruth points."""
    assert groundtruth_las.point_format == reader.point_format
    for i, points in enumerate(reader.chunk_iterator(iter_size)):
        expected_points = groundtruth_las.points[i * iter_size : (i + 1) * iter_size]
        for dim_name in points.array.dtype.names:
            assert np.allclose(expected_points[dim_name], points[dim_name]), f"{dim_name} not equal"


def test_that_chunked_reading_gives_expected_points(las_path_fixture):
    with pylas.open(las_path_fixture) as las_reader:
        with pylas.open(las_path_fixture) as reader:
            las = las_reader.read()
            check_chunked_reading_is_gives_expected_points(las, reader, iter_size=50)


def test_chunked_laz(all_laz_path, laz_backend):
    if not laz_backend:
        pytest.skip("No LazBackend installed")
    with pylas.open(all_laz_path) as las_reader:
        with pylas.open(all_laz_path, laz_backend=laz_backend) as laz_reader:
            expected_las = las_reader.read()
            check_chunked_reading_is_gives_expected_points(
                expected_las, laz_reader, iter_size=50
            )


def test_that_chunked_las_writing_gives_expected_points(las_path_fixture):
    original_las = pylas.read(las_path_fixture)
    iter_size = 51

    with io.BytesIO() as tmp_output:
        with pylas.open(
            tmp_output,
            mode="w",
            closefd=False,
            header=original_las.header,
            do_compress=False,
        ) as las:
            for i in range(int(math.ceil(len(original_las.points) / iter_size))):
                original_points = original_las.points[
                    i * iter_size : (i + 1) * iter_size
                ]
                las.write(original_points)

        tmp_output.seek(0)
        with pylas.open(tmp_output, closefd=False) as reader:
            check_chunked_reading_is_gives_expected_points(
                original_las, reader, iter_size
            )
