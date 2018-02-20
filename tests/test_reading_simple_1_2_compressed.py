import pytest

import pylas


@pytest.fixture()
def read_file():
    return pylas.open('simple.laz')


@pytest.fixture()
def get_header():
    f = pylas.open('simple.laz')
    return f.header


def test_raw_header(get_header):
    header = get_header
    assert header.file_signature == b'LASF'
