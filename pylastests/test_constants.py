import pylas


def test_vlr_header_size():
    assert pylas.vlr.VLR_HEADER_SIZE == 54


def test_header_sizes():
    assert pylas.headers.rawheader.LAS_HEADERS_SIZE['1.1'] == 227
    assert pylas.headers.rawheader.LAS_HEADERS_SIZE['1.2'] == 227


def test_lost_dims():
    assert set(pylas.lost_dimensions(3, 0)) == {
        'red', 'green', 'blue', 'gps_time'}
    assert set(pylas.lost_dimensions(2, 0)) == {'red', 'green', 'blue'}
    assert set(pylas.lost_dimensions(1, 0)) == {'gps_time'}

    assert set(pylas.lost_dimensions(0, 0)) == set()
    assert set(pylas.lost_dimensions(0, 1)) == set()
    assert set(pylas.lost_dimensions(0, 2)) == set()
    assert set(pylas.lost_dimensions(0, 3)) == set()
