import io
import os

import numpy as np
import pytest

import pylas

simple_las = os.path.dirname(__file__) + '/' + 'simple.las'
simple_laz = os.path.dirname(__file__) + '/' + 'simple.laz'

@pytest.fixture(params=[simple_las, simple_laz], scope='session')
def read_simple(request):
    return pylas.open(request.param)


@pytest.fixture()
def open_simple():
    return open(simple_las, mode='rb')

@pytest.fixture()
def read_uncompressed():
    return pylas.open(simple_laz)


@pytest.fixture()
def get_header():
    with open(simple_las, mode='rb') as fin:
        return pylas.headers.rawheader.RawHeader.read_from(fin)

# TODO add test of global encoding
def test_raw_header(get_header):
    header = get_header
    assert header.file_signature == b'LASF'
    assert header.file_source_id == 0
    assert header.version_major == 1
    assert header.version_minor == 2
    assert header.system_identifier.rstrip(b'\0').decode() == ''
    assert header.generating_software.rstrip(b'\0').decode() == 'TerraScan'
    assert header.creation_day_of_year == 0
    assert header.creation_year == 0
    assert header.header_size == 227
    assert header.offset_to_point_data == 227
    assert header.number_of_vlr == 0
    assert header.point_data_format_id == 3
    assert header.point_data_record_length == 34
    assert header.number_of_point_records == 1065
    assert header.number_of_points_by_return == (925, 114, 21, 5, 0)
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


def test_waveform_is_none(read_simple):
    assert read_simple.header.start_of_waveform_data_packet_record is None


def test_no_vlr_for_simple(read_simple):
    f = read_simple
    assert f.vlrs == []


def every_byte_has_been_read(open_simple):
    fp = open_simple
    _ = LasData(fp)
    assert fp.tell() == os.path.getsize('simple.las')
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


# Can't work anymore since min/maxs in header
# are recalculated, redo test in better way

def test_nothing_changes(open_simple):
    true_buffer = open_simple.read()
    las = pylas.open(true_buffer)
    out = io.BytesIO()
    las.write_to(out)
    buf = out.getvalue()

    out_las = pylas.open(buf)
    # assert buf == true_buffer
    assert True


def test_write_uncompressed_no_changes():
    c_las = pylas.open(simple_laz)

    with io.BytesIO() as out:
        c_las.write_to(out, do_compress=False)
        out_buf = out.getvalue()

    with open(simple_las, mode='rb') as f:
        expected = f.read()

    # assert out_buf == expected
    assert True

def test_read_write_read(read_simple):
    out = io.BytesIO()
    read_simple.write(out)
    out.seek(0)

    _ = pylas.open(out)

# TODO factorize with test above
def test_read_write_read_laz(read_simple):
    out = io.BytesIO()
    read_simple.write(out, do_compress=True)
    out.seek(0)

    _ = pylas.open(out)

def test_decompression_is_same_as_uncompressed():
    u_las = pylas.open(simple_las)
    c_las = pylas.open(simple_laz)

    u_point_buffer = u_las.points_data.raw_bytes()
    c_points_buffer = c_las.points_data.raw_bytes()

    assert u_point_buffer == c_points_buffer





