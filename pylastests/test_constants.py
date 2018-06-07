import pylas


def test_vlr_header_size():
    assert pylas.vlrs.rawvlr.VLR_HEADER_SIZE == 54


def test_header_sizes():
    assert pylas.headers.rawheader.LAS_HEADERS_SIZE["1.1"] == 227
    assert pylas.headers.rawheader.LAS_HEADERS_SIZE["1.2"] == 227
    assert pylas.headers.rawheader.LAS_HEADERS_SIZE["1.3"] == 235
    assert pylas.headers.rawheader.LAS_HEADERS_SIZE["1.4"] == 375


def test_lost_dims():
    assert set(pylas.lost_dimensions(3, 0)) == {"red", "green", "blue", "gps_time"}
    assert set(pylas.lost_dimensions(2, 0)) == {"red", "green", "blue"}
    assert set(pylas.lost_dimensions(1, 0)) == {"gps_time"}

    assert set(pylas.lost_dimensions(0, 0)) == set()
    assert set(pylas.lost_dimensions(0, 1)) == set()
    assert set(pylas.lost_dimensions(0, 2)) == set()
    assert set(pylas.lost_dimensions(0, 3)) == set()


def test_has_waveform():
    for i in (4, 5, 9, 10):
        assert pylas.point.dims.format_has_waveform_packet(
            i
        ), "Point format {} should have waveform".format(i)

    for i in (0, 1, 2, 3, 6, 7, 8):
        assert not pylas.point.dims.format_has_waveform_packet(
            i
        ), "Point format {} should not have waveform".format(i)


def test_extra_bytes_struct_size():
    assert pylas.vlrs.known.ExtraBytesStruct.size() == 192


def test_waveform_packet_struct_size():
    assert pylas.vlrs.known.WaveformPacketStruct.size() == 26
