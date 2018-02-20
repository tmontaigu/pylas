import pytest

import pylas


@pytest.fixture(params=['simple.las', 'simple.laz'])
def las(request):
    return pylas.open(request.param)


def test_classification_overflows(las):
    c = las.classification
    c[0] = 54
    with pytest.raises(OverflowError):
        las.classification = c
