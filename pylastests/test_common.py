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
plane_laz = os.path.dirname(__file__) + "/plane.laz"


def write_then_read_again(las, do_compress=False):
    out = io.BytesIO()
    las.write(out, do_compress=do_compress)
    out.seek(0)
    return pylas.read(out)


@pytest.fixture(
    params=[simple_las, simple_laz, vegetation1_3_las, test1_4_las, plane_laz, extra_bytes_laz, extra_bytes_las])
def las(request):
    return pylas.read(request.param)


@pytest.fixture(params=[simple_las, simple_laz, vegetation1_3_las])
def all_las_but_1_4(request):
    return pylas.read(request.param)


@pytest.fixture(params=[simple_las, vegetation1_3_las, test1_4_las, extra_bytes_las])
def las_path_fixture(request):
    return request.param


@pytest.fixture(params=[simple_laz, extra_bytes_laz, plane_laz])
def all_laz_path(request):
    return request.param


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
    assert las.points_data.point_format.id == 2
    assert las.header.point_format_id == 2
    assert las.header.version == in_version
    assert dim_does_not_exists(las, "gps_time")

    las = pylas.convert(las, point_format_id=1)
    las = write_then_read_again(las)
    assert las.points_data.point_format.id == 1
    assert las.header.point_format_id == 1
    assert las.header.version == in_version
    assert dim_does_not_exists(las, "red")
    assert dim_does_not_exists(las, "green")
    assert dim_does_not_exists(las, "blue")

    las = pylas.convert(las, point_format_id=0)
    las = write_then_read_again(las)
    assert las.points_data.point_format.id == 0
    assert las.header.point_format_id == 0
    assert las.header.version == in_version
    assert dim_does_not_exists(las, "red")
    assert dim_does_not_exists(las, "green")
    assert dim_does_not_exists(las, "blue")
    assert dim_does_not_exists(las, "gps_time")

    las = pylas.convert(las, point_format_id=8)
    las = write_then_read_again(las)
    assert las.header.version == "1.4"
    assert las.points_data.point_format.id == 8
    assert las.header.point_format_id == 8
    assert dim_does_exists(las, "red")
    assert dim_does_exists(las, "green")
    assert dim_does_exists(las, "blue")
    assert dim_does_exists(las, "nir")

    las = pylas.convert(las, point_format_id=7)
    las = write_then_read_again(las)
    assert las.header.version == "1.4"
    assert las.points_data.point_format.id == 7
    assert las.header.point_format_id == 7
    assert dim_does_exists(las, "red")
    assert dim_does_exists(las, "green")
    assert dim_does_exists(las, "blue")
    assert dim_does_not_exists(las, "nir")

    las = pylas.convert(las, point_format_id=6)
    las = write_then_read_again(las)
    assert las.header.version == "1.4"
    assert las.points_data.point_format.id == 6
    assert las.header.point_format_id == 6
    assert dim_does_not_exists(las, "red")
    assert dim_does_not_exists(las, "green")
    assert dim_does_not_exists(las, "blue")
    assert dim_does_not_exists(las, "nir")


def test_conversion_file_version():
    las = pylas.create(point_format_id=0, file_version='1.4')
    las2 = pylas.convert(las, file_version='1.2')

    assert las.points_data.point_format == las2.points_data.point_format
    for dim_name in las.points_data.point_format.dimension_names:
        assert np.allclose(
            las.points_data[dim_name], las2.points_data[dim_name]
        ), "{} not equal".format(dim_name)


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


def test_coords_do_not_break(las):
    xs, ys, zs = las.x, las.y, las.z

    las.x = xs
    las.y = ys
    las.z = zs

    assert np.allclose(xs, las.x)
    assert np.allclose(ys, las.y)
    assert np.allclose(zs, las.z)


def test_coords_when_setting_offsets_and_scales(las):
    new_las = pylas.create()

    new_las.header.offsets = las.header.offsets
    new_las.header.scales = las.header.scales

    new_las.x = las.x
    new_las.y = las.y
    new_las.z = las.z

    assert np.allclose(las.x, new_las.x)
    assert np.allclose(las.y, new_las.y)
    assert np.allclose(las.z, new_las.z)


def test_coords_when_using_create_from_header(las):
    new_las = pylas.create_from_header(las.header)

    new_las.x = las.x
    new_las.y = las.y
    new_las.z = las.z

    assert np.allclose(las.x, new_las.x)
    assert np.allclose(las.y, new_las.y)
    assert np.allclose(las.z, new_las.z)


def test_slicing(las):
    las.points = las.points[len(las.points) // 2:]


def test_can_write_then_re_read_files(las):
    las = write_then_read_again(las, do_compress=las.points_data.point_format.id < 6)
