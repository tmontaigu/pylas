from pylas.headers.lasheader import Header


def test_1_2_to_raw():
    header = Header(version='1.2', point_format=0)
    raw = header.into_raw()

    assert raw.version_major == 1
    assert raw.version_minor == 2
    assert raw.generating_software == b'pylas' + b'\x00' * (32 - len(b'pylas'))
    assert raw.header_size == 227
    # assert raw.offset_to_point_data == raw.header_size
    assert raw.point_data_format_id == 0
