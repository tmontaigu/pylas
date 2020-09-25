import os

import numpy as np
import pytest

import pylas
from pylastests.test_common import (
    simple_las,
    simple_laz,
    write_then_read_again,
    do_compression,
)


@pytest.fixture(
    params=[simple_las, simple_laz]
    if pylas.LazBackend.detect_available()
    else [simple_las],
    scope="session",
)
def read_simple(request):
    return pylas.read(request.param)


@pytest.fixture()
def open_simple():
    return open(simple_las, mode="rb")


@pytest.fixture()
def read_uncompressed():
    return pylas.read(simple_laz)


@pytest.fixture()
def get_header():
    with pylas.open(simple_las) as fin:
        return fin.header


# TODO add test of global encoding
def test_raw_header(get_header):
    header = get_header
    assert header.file_signature == b"LASF"
    assert header.file_source_id == 0
    assert header.version_major == 1
    assert header.version_minor == 2
    assert header.system_identifier.rstrip(b"\0").decode() == ""
    assert header.generating_software.rstrip(b"\0").decode() == "TerraScan"
    assert header.creation_day_of_year == 0
    assert header.creation_year == 0
    assert header.size == 227
    assert header.offset_to_point_data == 227
    assert header.number_of_vlr == 0
    assert header.point_format_id == 3
    assert header.point_data_record_length == 34
    assert header.point_count == 1065
    assert tuple(header.number_of_points_by_return) == (925, 114, 21, 5, 0)
    assert header.x_scale == 0.01
    assert header.y_scale == 0.01
    assert header.z_scale == 0.01
    assert header.x_offset == 0
    assert header.y_offset == 0
    assert header.z_offset == 0
    assert header.x_max == pytest.approx(638982.55)
    assert header.x_min == pytest.approx(635619.85)
    assert header.y_max == pytest.approx(853535.43)
    assert header.y_min == pytest.approx(848899.70)
    assert header.z_max == pytest.approx(586.38)
    assert header.z_min == pytest.approx(406.59)


def test_no_vlr_for_simple(read_simple):
    f = read_simple
    assert f.vlrs == []


def test_every_byte_has_been_read(open_simple):
    fp = open_simple
    _ = pylas.read(fp, closefd=False)
    assert fp.tell() == os.path.getsize(simple_las)
    fp.close()


def test_unscaled_x(read_simple):
    f = read_simple
    assert f.X.max() == 63898255
    assert f.X.min() == 63561985


def test_unscaled_y(read_simple):
    f = read_simple
    assert f.Y.max() == 85353543
    assert f.Y.min() == 84889970


def test_unscaled_z(read_simple):
    f = read_simple
    assert f.Z.max() == 58638
    assert f.Z.min() == 40659


def test_intensity(read_simple):
    f = read_simple
    assert f.intensity.max() == 254
    assert f.intensity.min() == 0


def test_return_number(read_simple):
    f = read_simple
    assert f.return_number.max() == 4
    assert f.return_number.min() == 1


def test_number_of_returns(read_simple):
    f = read_simple
    assert f.number_of_returns.max() == 4
    assert f.number_of_returns.min() == 1


def test_edge_of_flight_line(read_simple):
    f = read_simple
    assert f.edge_of_flight_line.max() == 0
    assert f.edge_of_flight_line.min() == 0


def test_scan_direction_flag(read_simple):
    f = read_simple
    assert f.scan_direction_flag.max() == 1
    assert f.scan_direction_flag.min() == 0


def test_scan_angle_rank(read_simple):
    f = read_simple
    assert f.scan_angle_rank.max() == 18
    assert f.scan_angle_rank.min() == -19


def test_classification_max_min(read_simple):
    f = read_simple
    assert f.classification.max() == 2
    assert f.classification.min() == 1


def test_classification_count(read_simple):
    f = read_simple
    uniques, counts = np.unique(f.classification, return_counts=True)
    assert np.all(uniques == [1, 2])
    assert counts[0] == 789  # class code 1
    assert counts[1] == 276  # class code 2


def test_user_data(read_simple):
    f = read_simple
    assert f.user_data.max() == 149
    assert f.user_data.min() == 117


def test_point_source_id(read_simple):
    f = read_simple
    assert f.point_source_id.max() == 7334
    assert f.point_source_id.min() == 7326


def test_gps_time(read_simple):
    f = read_simple
    assert f.gps_time.max() == pytest.approx(249783.162158)
    assert f.gps_time.min() == pytest.approx(245370.417075)


def test_red(read_simple):
    f = read_simple
    assert f.red.max() == 249
    assert f.red.min() == 39


def test_green(read_simple):
    f = read_simple
    assert f.green.max() == 239
    assert f.green.min() == 57


def test_blue(read_simple):
    f = read_simple
    assert f.blue.max() == 249
    assert f.blue.min() == 56


@pytest.mark.parametrize("do_compress", do_compression)
def test_read_write_read(read_simple, do_compress):
    _ = write_then_read_again(read_simple, do_compress=do_compress)


@pytest.mark.skipif(
    len(pylas.LazBackend.detect_available()) == 0, reason="No Laz Backend installed"
)
def test_decompression_is_same_as_uncompressed():
    u_las = pylas.read(simple_las)
    c_las = pylas.read(simple_laz)

    u_point_buffer = u_las.points.raw_bytes()
    c_points_buffer = c_las.points.raw_bytes()

    assert u_point_buffer == c_points_buffer
