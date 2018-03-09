import io
import os

import numpy as np
import pytest

import pylas

do_compression = [False, True]

simple_las = os.path.dirname(__file__) + '/' + 'simple.las'
simple_laz = os.path.dirname(__file__) + '/' + 'simple.laz'
vegetation1_3_las = os.path.dirname(__file__) + '/vegetation_1_3.las'
test1_4_las = os.path.dirname(__file__) + '/' + 'test1_4.las'


@pytest.fixture(params=[simple_las, simple_laz, vegetation1_3_las, test1_4_las])
def las(request):
    return pylas.open(request.param)


def dim_does_not_exists(las, dim_name):
    try:
        _ = getattr(las, dim_name)
    except ValueError:
        return True
    return False


def dim_does_exists(las, dim_name):
    try:
        _ = getattr(las, dim_name)
    except ValueError:
        return False
    return True

# TODO: should propably use ALL_POiNTS_FORMATS_DIMS dict
# to do this test


def test_change_format(las):
    in_version = las.header.version

    las = pylas.convert(las, point_format_id=2)
    assert las.points_data.point_format_id == 2
    assert las.header.point_data_format_id == 2
    assert las.header.version == in_version
    assert dim_does_not_exists(las, 'gps_time')

    las = pylas.convert(las, point_format_id=1)
    assert las.points_data.point_format_id == 1
    assert las.header.point_data_format_id == 1
    assert las.header.version == in_version
    assert dim_does_not_exists(las, 'red')
    assert dim_does_not_exists(las, 'green')
    assert dim_does_not_exists(las, 'blue')

    las = pylas.convert(las, point_format_id=0)
    assert las.points_data.point_format_id == 0
    assert las.header.point_data_format_id == 0
    assert las.header.version == in_version
    assert dim_does_not_exists(las, 'red')
    assert dim_does_not_exists(las, 'green')
    assert dim_does_not_exists(las, 'blue')
    assert dim_does_not_exists(las, 'gps_time')

    las = pylas.convert(las, point_format_id=8)
    assert las.header.version == '1.4'
    assert las.points_data.point_format_id == 8
    assert las.header.point_data_format_id == 8
    assert dim_does_exists(las, 'red')
    assert dim_does_exists(las, 'green')
    assert dim_does_exists(las, 'blue')
    assert dim_does_exists(las, 'nir')

    las = pylas.convert(las, point_format_id=7)
    assert las.header.version == '1.4'
    assert las.points_data.point_format_id == 7
    assert las.header.point_data_format_id == 7
    assert dim_does_exists(las, 'red')
    assert dim_does_exists(las, 'green')
    assert dim_does_exists(las, 'blue')
    assert dim_does_not_exists(las, 'nir')

    las = pylas.convert(las, point_format_id=6)
    assert las.header.version == '1.4'
    assert las.points_data.point_format_id == 6
    assert las.header.point_data_format_id == 6
    assert dim_does_not_exists(las, 'red')
    assert dim_does_not_exists(las, 'green')
    assert dim_does_not_exists(las, 'blue')
    assert dim_does_not_exists(las, 'nir')


def test_rw_all_set_one(las):
    for dim_name in las.points_data.dimensions_names:
        field = las[dim_name]
        field[:] = 1
        las[dim_name] = field

    for dim_name in las.points_data.dimensions_names:
        assert np.alltrue(las[dim_name] == 1)

    out = io.BytesIO()

    las.write(out)
    out.seek(0)

    las2 = pylas.open(out)

    for dim_name in las.points_data.dimensions_names:
        assert np.alltrue(las[dim_name] == las2[dim_name])
