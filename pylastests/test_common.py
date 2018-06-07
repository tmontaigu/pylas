import io
import os

import numpy as np
import pytest

import pylas

do_compression = [False, True]

simple_las = os.path.dirname(__file__) + "/" + "simple.las"
simple_laz = os.path.dirname(__file__) + "/" + "simple.laz"
vegetation1_3_las = os.path.dirname(__file__) + "/vegetation_1_3.las"
test1_4_las = os.path.dirname(__file__) + "/" + "test1_4.las"
extra_bytes_las = os.path.dirname(__file__) + "/extrabytes.las"
extra_bytes_laz = os.path.dirname(__file__) + "/extra.laz"


def write_then_read_again(las, do_compress=False):
    out = io.BytesIO()
    las.write(out, do_compress=do_compress)
    out.seek(0)
    return pylas.read(out)


@pytest.fixture(params=[simple_las, simple_laz, vegetation1_3_las, test1_4_las])
def las(request):
    return pylas.read(request.param)


@pytest.fixture(params=[simple_las, simple_laz, vegetation1_3_las])
def all_las_but_1_4(request):
    return pylas.read(request.param)


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
    las = write_then_read_again(las)
    assert las.points_data.point_format_id == 2
    assert las.header.point_format_id == 2
    assert las.header.version == in_version
    assert dim_does_not_exists(las, "gps_time")

    las = pylas.convert(las, point_format_id=1)
    las = write_then_read_again(las)
    assert las.points_data.point_format_id == 1
    assert las.header.point_format_id == 1
    assert las.header.version == in_version
    assert dim_does_not_exists(las, "red")
    assert dim_does_not_exists(las, "green")
    assert dim_does_not_exists(las, "blue")

    las = pylas.convert(las, point_format_id=0)
    las = write_then_read_again(las)
    assert las.points_data.point_format_id == 0
    assert las.header.point_format_id == 0
    assert las.header.version == in_version
    assert dim_does_not_exists(las, "red")
    assert dim_does_not_exists(las, "green")
    assert dim_does_not_exists(las, "blue")
    assert dim_does_not_exists(las, "gps_time")

    las = pylas.convert(las, point_format_id=8)
    las = write_then_read_again(las)
    assert las.header.version == "1.4"
    assert las.points_data.point_format_id == 8
    assert las.header.point_format_id == 8
    assert dim_does_exists(las, "red")
    assert dim_does_exists(las, "green")
    assert dim_does_exists(las, "blue")
    assert dim_does_exists(las, "nir")

    las = pylas.convert(las, point_format_id=7)
    las = write_then_read_again(las)
    assert las.header.version == "1.4"
    assert las.points_data.point_format_id == 7
    assert las.header.point_format_id == 7
    assert dim_does_exists(las, "red")
    assert dim_does_exists(las, "green")
    assert dim_does_exists(las, "blue")
    assert dim_does_not_exists(las, "nir")

    las = pylas.convert(las, point_format_id=6)
    las = write_then_read_again(las)
    assert las.header.version == "1.4"
    assert las.points_data.point_format_id == 6
    assert las.header.point_format_id == 6
    assert dim_does_not_exists(las, "red")
    assert dim_does_not_exists(las, "green")
    assert dim_does_not_exists(las, "blue")
    assert dim_does_not_exists(las, "nir")


# TODO: okay, so onversion from/to fmt <6 and > 6
# cannot be tested like this becasue some fieds have more bits some there are some conversion 'issues'


def test_conversion_copies_fields(all_las_but_1_4):
    las = all_las_but_1_4
    for i in (0, 1, 2, 3, 2, 1, 0):
        old_record = las.points_data
        las = pylas.convert(las, point_format_id=i)
        las = write_then_read_again(las)

        for dim_name in old_record.dimensions_names:
            try:
                assert np.allclose(
                    las.points_data[dim_name], old_record[dim_name]
                ), "{} not equal".format(dim_name)
            except ValueError:
                pass  # dim exists in old_record but not new


def test_rw_all_set_one(las):
    for dim_name in las.points_data.dimensions_names:
        field = las[dim_name]
        field[:] = 1
        las[dim_name] = field

    for dim_name in las.points_data.dimensions_names:
        assert np.alltrue(las[dim_name] == 1), "{} not equal".format(dim_name)

    las2 = write_then_read_again(las)

    for dim_name in las.points_data.dimensions_names:
        assert np.alltrue(las[dim_name] == las2[dim_name]), "{} not equal".format(
            dim_name
        )
