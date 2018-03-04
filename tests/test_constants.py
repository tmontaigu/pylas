import pylas


def test_vlr_header_size():
    assert pylas.vlr.VLR_HEADER_SIZE == 54


def test_header_sizes():
    assert pylas.headers.rawheader.LAS_HEADERS_SIZE['1.1'] == 227
    assert pylas.headers.rawheader.LAS_HEADERS_SIZE['1.2'] == 227
