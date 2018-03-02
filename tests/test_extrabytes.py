import pytest

import pylas


@pytest.fixture()
def extrab_las():
    return pylas.open('extrabytes.las')


def test_extra_names(extrab_las):
    all_dims = set(extrab_las.points_data.array.dtype.names)

    assert "Colors" in all_dims
    assert "Intensity" in all_dims
    assert "Flags" in all_dims
    assert "Reserved" in all_dims
    assert "Time" in all_dims
