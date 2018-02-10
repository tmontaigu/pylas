import pytest
from pylas.lasdata import LasData


@pytest.fixture()
def read_simple():
    return LasData.from_file('simple.las')


def test_raw_header(read_simple):
    f = read_simple
    header = f.header
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
