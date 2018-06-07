import numpy as np
import pytest

import pylas
from pylastests.test_common import (
    do_compression,
    simple_las,
    simple_laz,
    write_then_read_again,
)


@pytest.fixture(params=[simple_las, simple_laz])
def las(request):
    return pylas.read(request.param)


def test_classification_overflows(las):
    if not pylas.lib.USE_UNPACKED:
        c = las.classification
        c[0] = 54
        with pytest.raises(OverflowError):
            las.classification = c
    else:
        las.classification[0] = 54
        with pytest.raises(OverflowError):
            las.points_data.repack_sub_fields()


@pytest.mark.parametrize("do_compress", do_compression)
def test_classification_change(las, do_compress):
    c = las.classification
    c[:] = 10

    las.classification = c
    assert np.allclose(c, las.classification)

    las = write_then_read_again(las, do_compress=do_compress)
    assert np.allclose(c, las.classification)


@pytest.mark.parametrize("do_compress", do_compression)
def test_synthetic_change(las, do_compress):
    s = las.synthetic
    s[:] = False
    s[17] = True

    las.synthetic = s
    assert np.allclose(s, las.synthetic)
    las = write_then_read_again(las, do_compress=do_compress)

    assert np.allclose(s, las.synthetic)


@pytest.mark.parametrize("do_compress", do_compression)
def test_key_point_change(las, do_compress):
    kp = las.key_point
    kp[:] = False
    kp[25] = True

    las.key_point = kp
    assert np.allclose(kp, las.key_point)

    las = write_then_read_again(las, do_compress=do_compress)
    assert np.allclose(kp, las.key_point)


@pytest.mark.parametrize("do_compress", do_compression)
def test_withheld_changes(las, do_compress):
    withheld = las.withheld
    withheld[:] = False
    withheld[180] = True

    las.withheld = withheld
    assert np.allclose(withheld, las.withheld)

    las = write_then_read_again(las, do_compress=do_compress)

    assert np.allclose(withheld, las.withheld)
