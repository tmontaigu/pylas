import numpy as np
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


def test_classification_change(tmpdir, las):
    c = las.classification
    c[:] = 10

    las.classification = c
    assert np.allclose(c, las.classification)

    out = tmpdir.join('tmp.las').open('wb')
    las.write_to(out)
    out.close()

    out = tmpdir.join('tmp.las').open('rb')
    las = pylas.open(out)

    assert np.allclose(c, las.classification)


def test_synthetic_change(tmpdir, las):
    s = las.synthetic
    s[:] = False
    s[17] = True

    las.synthetic = s
    assert np.allclose(s, las.synthetic)

    out = tmpdir.join('tmp.las').open('wb')
    las.write_to(out)
    out.close()

    out = tmpdir.join('tmp.las').open('rb')
    las = pylas.open(out)

    assert np.allclose(s, las.synthetic)


def test_key_point_change(tmpdir, las):
    kp = las.key_point
    kp[:] = False
    kp[25] = True

    las.key_point = kp
    assert np.allclose(kp, las.key_point)

    out = tmpdir.join('tmp.las').open('wb')
    las.write_to(out)
    out.close()

    out = tmpdir.join('tmp.las').open('rb')
    las = pylas.open(out)

    assert np.allclose(kp, las.key_point)


def test_withheld_changes(tmpdir, las):
    withheld = las.withheld
    withheld[:] = False
    withheld[180] = True

    las.withheld = withheld
    assert np.allclose(withheld, las.withheld)

    out = tmpdir.join('tmp.las').open('wb')
    las.write_to(out)
    out.close()

    out = tmpdir.join('tmp.las').open('rb')
    las = pylas.open(out)

    assert np.allclose(withheld, las.withheld)


def dim_does_not_exists(las, dim_name):
    try:
        _ = getattr(las, dim_name)
    except ValueError:
        return True
    return False


def test_change_format(las):
    assert las.points_data.point_format_id == 3
    assert las.header.point_data_format_id == 3

    las.to_point_format(2)
    assert las.points_data.point_format_id == 2
    assert las.header.point_data_format_id == 2
    assert dim_does_not_exists(las, 'gps_time')

    las.to_point_format(1)
    assert las.points_data.point_format_id == 1
    assert las.header.point_data_format_id == 1
    assert dim_does_not_exists(las, 'red')
    assert dim_does_not_exists(las, 'green')
    assert dim_does_not_exists(las, 'blue')

    las.to_point_format(0)
    assert las.points_data.point_format_id == 0
    assert las.header.point_data_format_id == 0
    assert dim_does_not_exists(las, 'red')
    assert dim_does_not_exists(las, 'green')
    assert dim_does_not_exists(las, 'blue')
    assert dim_does_not_exists(las, 'gps_time')
