import numpy as np
import pytest

import pylas
from tests.test_common import test1_4_las, extra_bytes_las
from tests.test_creation import write_then_read_again


@pytest.fixture()
def extrab_las():
    return pylas.open(extra_bytes_las)


@pytest.fixture()
def las1_4():
    return pylas.open(test1_4_las)


def test_extra_names(extrab_las):
    all_dims = set(extrab_las.points_data.array.dtype.names)

    assert "Colors" in all_dims
    assert "Intensity" in all_dims
    assert "Flags" in all_dims
    assert "Reserved" in all_dims
    assert "Time" in all_dims


def test_add_extra_bytes(las1_4):
    las1_4.add_extra_dim('test_dim', 'u1')
    las1_4.add_extra_dim('test_array', '3f8')

    las1_4.test_dim[:] = 150
    las1_4.test_array[:, 0] = 1.1
    las1_4.test_array[:, 1] = 2.2
    las1_4.test_array[:, 2] = 333.6

    las1_4 = write_then_read_again(las1_4)

    assert np.alltrue(las1_4.test_dim == 150)
    assert np.allclose(las1_4.test_array[:, 0], 1.1)
    assert np.allclose(las1_4.test_array[:, 1], 2.2)
    assert np.allclose(las1_4.test_array[:, 2], 333.6)
