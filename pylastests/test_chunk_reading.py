import numpy as np
import pytest

import pylas
# noinspection PyUnresolvedReferences
from pylastests.test_common import all_laz_path
from pylas import LazBackend


@pytest.fixture(params=LazBackend.detect_available())
def laz_backend(request):
    return request.param


def check_chunked_reading_is_gives_expected_points(reader_groundtruth, reader, iter_size):
    """ Checks that the points read by the reader are the same as points read by the
    groundtruth reader.
    """
    las = reader_groundtruth.read()
    assert las.point_format == reader.point_format
    for i, points in enumerate(reader.chunk_iterator(iter_size)):
        expected_points = las.points[i * iter_size: (i + 1) * iter_size]
        for dim_name in points.array.dtype.names:
            assert np.allclose(expected_points[dim_name], points[dim_name])


def test_that_chunked_reading_gives_expected_points(las_path_fixture):
    with pylas.open(las_path_fixture) as las_reader:
        with pylas.open(las_path_fixture) as reader:
            check_chunked_reading_is_gives_expected_points(las_reader, reader, iter_size=50)


def test_chunked_laz(all_laz_path, laz_backend):
    if not laz_backend:
        pytest.skip("No LazBackend installed")
    with pylas.open(all_laz_path) as las_reader:
        with pylas.open(all_laz_path, laz_backends=(laz_backend,)) as laz_reader:
            check_chunked_reading_is_gives_expected_points(las_reader, laz_reader, iter_size=50)
