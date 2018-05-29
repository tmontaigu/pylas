import numpy as np
import pytest

import pylas
from pylastests.test_common import test1_4_las, extra_bytes_las, write_then_read_again, extra_bytes_laz, simple_las


@pytest.fixture(params=[extra_bytes_las, extra_bytes_laz])
def extrab_las(request):
    return pylas.read(request.param)


@pytest.fixture()
def las1_4():
    return pylas.read(test1_4_las)


def test_extra_dim_spec():
    extra_dims_specs = [('codification', 'u4')]
    dtype = pylas.point.dims.get_dtype_of_format_id(0)
    dtype = pylas.point.dims.dtype_append(dtype, extra_dims_specs)

    found_extra_dims_spec = pylas.point.dims.get_extra_dimensions_spec(dtype, 0)

    assert found_extra_dims_spec == extra_dims_specs


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


def test_extra_dimensions_names_property():
    simple = pylas.read(simple_las)
    assert simple.points_data.extra_dimensions_names == set()

    extra = pylas.read(extra_bytes_las)
    assert extra.points_data.extra_dimensions_names == {'Colors', 'Intensity', 'Flags', 'Reserved', 'Time'}
