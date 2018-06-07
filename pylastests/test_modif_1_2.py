import numpy as np
import pytest

import pylas
from pylastests.test_common import do_compression, simple_las, simple_laz


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
def test_classification_change(tmpdir, las, do_compress):
    c = las.classification
    c[:] = 10

    las.classification = c
    assert np.allclose(c, las.classification)

    out = tmpdir.join("tmp.las").open("wb")
    las.write_to(out, do_compress=do_compress)
    out.close()

    out = tmpdir.join("tmp.las").open("rb")
    las = pylas.read(out)

    assert np.allclose(c, las.classification)


@pytest.mark.parametrize("do_compress", do_compression)
def test_synthetic_change(tmpdir, las, do_compress):
    s = las.synthetic
    s[:] = False
    s[17] = True

    las.synthetic = s
    assert np.allclose(s, las.synthetic)

    out = tmpdir.join("tmp.las").open("wb")
    las.write_to(out, do_compress=do_compress)
    out.close()

    out = tmpdir.join("tmp.las").open("rb")
    las = pylas.read(out)

    assert np.allclose(s, las.synthetic)


@pytest.mark.parametrize("do_compress", do_compression)
def test_key_point_change(tmpdir, las, do_compress):
    kp = las.key_point
    kp[:] = False
    kp[25] = True

    las.key_point = kp
    assert np.allclose(kp, las.key_point)

    out = tmpdir.join("tmp.las").open("wb")
    las.write_to(out, do_compress=do_compress)
    out.close()

    out = tmpdir.join("tmp.las").open("rb")
    las = pylas.read(out)

    assert np.allclose(kp, las.key_point)


@pytest.mark.parametrize("do_compress", do_compression)
def test_withheld_changes(tmpdir, las, do_compress):
    withheld = las.withheld
    withheld[:] = False
    withheld[180] = True

    las.withheld = withheld
    assert np.allclose(withheld, las.withheld)

    out = tmpdir.join("tmp.las").open("wb")
    las.write_to(out, do_compress)
    out.close()

    out = tmpdir.join("tmp.las").open("rb")
    las = pylas.read(out)

    assert np.allclose(withheld, las.withheld)
