import numpy as np
import pytest

import pylas
from pylastests.test_common import test1_4_las, write_then_read_again


@pytest.fixture(scope="session")
def las():
    return pylas.read(test1_4_las)


def test_classification(las):
    las.classification[:] = 234
    assert np.alltrue(las.classification == 234)

    res = write_then_read_again(las)

    assert np.alltrue(las.classification == res.classification)


def test_intensity(las):
    las.intensity[:] = 89
    assert np.alltrue(las.intensity == 89)
    res = write_then_read_again(las)

    assert np.alltrue(las.intensity == res.intensity)
