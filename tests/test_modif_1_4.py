import io
import os

import numpy as np
import pylas
import pytest

test1_4_las = os.path.dirname(__file__) + '/' + 'test1_4.las'


@pytest.fixture(scope='session')
def las():
    return pylas.open(test1_4_las)


@pytest.fixture()
def out():
    return io.BytesIO()


def test_classification(las, out):
    las.classification[:] = 234
    assert np.alltrue(las.classification == 234)

    las.write(out)
    out.seek(0)

    res = pylas.open(out)
    assert np.alltrue(las.classification == res.classification)


def test_intensity(las, out):
    las.intensity[:] = 89
    assert np.alltrue(las.intensity == 89)

    las.write(out)
    out.seek(0)

    res = pylas.open(out)
    assert np.alltrue(las.intensity == res.intensity)
