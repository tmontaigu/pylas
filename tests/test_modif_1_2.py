import numpy as np
import io
import pytest
import os
import pylas

do_compression = [False, True]

simple_las = os.path.dirname(__file__) + '/' + 'simple.las'
simple_laz = os.path.dirname(__file__) + '/' + 'simple.laz'

@pytest.fixture(params=[simple_las, simple_laz])
def las(request):
    return pylas.open(request.param)


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

    out = tmpdir.join('tmp.las').open('wb')
    las.write_to(out, do_compress=do_compress)
    out.close()

    out = tmpdir.join('tmp.las').open('rb')
    las = pylas.open(out)

    assert np.allclose(c, las.classification)


@pytest.mark.parametrize("do_compress", do_compression)
def test_synthetic_change(tmpdir, las, do_compress):
    s = las.synthetic
    s[:] = False
    s[17] = True

    las.synthetic = s
    assert np.allclose(s, las.synthetic)

    out = tmpdir.join('tmp.las').open('wb')
    las.write_to(out, do_compress=do_compress)
    out.close()

    out = tmpdir.join('tmp.las').open('rb')
    las = pylas.open(out)

    assert np.allclose(s, las.synthetic)


@pytest.mark.parametrize("do_compress", do_compression)
def test_key_point_change(tmpdir, las, do_compress):
    kp = las.key_point
    kp[:] = False
    kp[25] = True

    las.key_point = kp
    assert np.allclose(kp, las.key_point)

    out = tmpdir.join('tmp.las').open('wb')
    las.write_to(out, do_compress=do_compress)
    out.close()

    out = tmpdir.join('tmp.las').open('rb')
    las = pylas.open(out)

    assert np.allclose(kp, las.key_point)


@pytest.mark.parametrize("do_compress", do_compression)
def test_withheld_changes(tmpdir, las, do_compress):
    withheld = las.withheld
    withheld[:] = False
    withheld[180] = True

    las.withheld = withheld
    assert np.allclose(withheld, las.withheld)

    out = tmpdir.join('tmp.las').open('wb')
    las.write_to(out, do_compress)
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


# TODO this test is copy pasted in test_modif_1_4.py
# should be factorized
def test_rw_all_set_one(las):
    for dim_name in las.points_data.dimensions_names:
        field = las[dim_name]
        field[:] = 1
        las[dim_name] = field

    for dim_name in las.points_data.dimensions_names:
        assert np.alltrue(las[dim_name] == 1)


    out = io.BytesIO()

    las.write(out)
    out.seek(0)

    las2 = pylas.open(out)

    for dim_name in las.points_data.dimensions_names:
        assert np.alltrue(las[dim_name] == las2[dim_name])