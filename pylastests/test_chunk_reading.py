import numpy as np
import pytest

import pylas
from pylas import LazBackend
from pylas.compression import find_laszip_executable
# noinspection PyUnresolvedReferences
from pylastests.test_common import las_path_fixture, all_laz_path


def get_available_laz_backends():
    available_backends = []
    for backend in LazBackend.all():
        if backend == LazBackend.Laszip:
            try:
                find_laszip_executable()
            except RuntimeError:
                pass
            else:
                available_backends.append(backend)
        elif backend == LazBackend.LazrsParallel:
            available_backends.append(backend)

    return available_backends


@pytest.fixture(params=get_available_laz_backends())
def laz_backend(request):
    return request.param


def check_chunked_reading_is_gives_expected_points(reader_gt, reader, iter_size):
    las = reader_gt.read()
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
    with pylas.open(all_laz_path) as las_reader:
        with pylas.open(all_laz_path, laz_backends=(laz_backend,)) as laz_reader:
            check_chunked_reading_is_gives_expected_points(las_reader, laz_reader, iter_size=50)
