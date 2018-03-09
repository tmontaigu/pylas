import io
import os

import numpy as np
import pytest

import pylas

simple_las = os.path.dirname(__file__) + '/' + 'simple.las'


@pytest.fixture()
def file():
    return pylas.open(simple_las)


def test_incompatible_data_type():
    las = pylas.create_las()
    dtype = np.dtype([('X', 'u4'), ('Y', 'u4'), ('Z', 'u4'),
                      ('codification', 'u4'), ('intensity', 'i2')])
    with pytest.raises(pylas.errors.IncompatibleDataFormat):
        las.points = np.zeros(120, dtype=dtype)


def test_xyz():
    las = pylas.create_las()
    shape = (150,)
    las.X = np.zeros(shape, dtype=np.int32)
    las.Y = np.ones(shape, dtype=np.int32)
    las.Z = np.zeros(shape, dtype=np.int32)
    las.Z[:] = -152

    out = io.BytesIO()
    las.write(out)
    out.seek(0)

    las = pylas.open(out)
    assert np.alltrue(las.X == 0)
    assert np.alltrue(las.Y == 1)
    assert np.alltrue(las.Z == -152)


def test_wrong_version():
    for i in range(6, 8):
        with pytest.raises(ValueError):
            _ = pylas.create_las(point_format=i, file_version='1.2')


def test_good_version_is_used():
    for i in range(6, 8):
        las = pylas.create_las(point_format=i)
        assert las.header.version_major == 1
        assert las.header.version_minor == 4


def test_extraction(file):
    new = pylas.create_las(point_format=0)

    assert file.points_data.point_format_id == 3

    # automatic promotion of point format
    new.points = file.points[file.classification == 2]
    assert new.points_data.point_format_id == 3

    assert len(new.points) == sum(file.classification == 2)
    assert np.alltrue(new.classification == 2)

    out = io.BytesIO()

    new.write(out)
    out.seek(0)

    file = pylas.open(out)
    assert np.alltrue(file.classification == 2)
