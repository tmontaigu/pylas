import numpy as np
import pytest

import pylas
from pylas.compression import find_laszip_executable
from pylastests.test_common import (
    test1_4_las,
    extra_bytes_las,
    write_then_read_again,
    extra_bytes_laz,
    simple_las,
)

extra_bytes_files = [extra_bytes_las]
# Because currently lazperf cannot decompress 1.4 file with extra dim
# and Travis CI doesn't have laszip installed
try:
    find_laszip_executable()
    extra_bytes_files.append(extra_bytes_laz)
except FileNotFoundError:
    pass


@pytest.fixture(params=extra_bytes_files)
def extrab_las(request):
    return pylas.read(request.param)


@pytest.fixture()
def las1_4():
    return pylas.read(test1_4_las)


def test_extra_names(extrab_las):
    all_dims = set(extrab_las.points.array.dtype.names)

    assert "Colors" in all_dims
    assert "Intensity" in all_dims
    assert "Flags" in all_dims
    assert "Reserved" in all_dims
    assert "Time" in all_dims


def test_add_extra_bytes(las1_4):
    las1_4.add_extra_dim("test_dim", "uint8")
    las1_4.add_extra_dim("test_array", "3f8")

    las1_4.test_dim[:] = 150
    las1_4.test_array[:, 0] = 1.1
    las1_4.test_array[:, 1] = 2.2
    las1_4.test_array[:, 2] = 333.6

    assert np.alltrue(las1_4.points["test_dim"] == 150)
    assert np.allclose(las1_4.points["test_array"][:, 0], 1.1)
    assert np.allclose(las1_4.points["test_array"][:, 1], 2.2)
    assert np.allclose(las1_4.points["test_array"][:, 2], 333.6)

    las1_4 = write_then_read_again(las1_4)

    assert np.alltrue(las1_4.test_dim == 150)
    assert np.allclose(las1_4.test_array[:, 0], 1.1)
    assert np.allclose(las1_4.test_array[:, 1], 2.2)
    assert np.allclose(las1_4.test_array[:, 2], 333.6)


def test_extra_bytes_well_saved(extrab_las):
    extrab_las.Time = np.zeros_like(extrab_las.Time)

    assert np.alltrue(extrab_las.points["Time"] == 0)

    extrab_las = write_then_read_again(extrab_las)

    assert np.alltrue(extrab_las.Time == 0)


def test_extra_dimensions_names_property():
    simple = pylas.read(simple_las)
    assert list(simple.points.extra_dimensions_names) == []

    extra = pylas.read(extra_bytes_las)
    expected_names = [
        "Colors",
        "Reserved",
        "Flags",
        "Intensity",
        "Time",
    ]
    assert expected_names == list(extra.points.extra_dimensions_names)


def test_conversion_keeps_eb(extrab_las):
    eb_0 = pylas.convert(extrab_las, point_format_id=0)

    assert (
        list(eb_0.points.extra_dimensions_names)
        == list(extrab_las.points.extra_dimensions_names)
    )
    for name in eb_0.points.extra_dimensions_names:
        assert np.allclose(eb_0[name], extrab_las[name])

    eb_0 = pylas.lib.write_then_read_again(eb_0)
    assert (
        list(eb_0.points.extra_dimensions_names)
        == list(extrab_las.points.extra_dimensions_names)
    )
    for name in eb_0.points.extra_dimensions_names:
        assert np.allclose(eb_0[name], extrab_las[name])
