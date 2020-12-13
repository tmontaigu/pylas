import io
import os

import pytest

import pylas
from pylastests.test_common import simple_laz


def test_append(file_path):
    """
    Test appending
    """
    if file_path.suffix == '.laz' and not pylas.LazBackend.Lazrs.is_available():
        pytest.skip("Only Lazrs backed supports appending")
    append_self_and_check(file_path)


def test_raises_for_laszip_backend():
    with pytest.raises(pylas.PylasError):
        with pylas.open(simple_laz, mode="a", laz_backend=pylas.LazBackend.Laszip):
            ...


def test_append_las_with_evlrs():
    las = append_self_and_check(os.path.dirname(__file__) + "/1_4_w_evlr.las")

    expected_evlr = pylas.EVLR(user_id="pylastest", record_id=42, description="just a test evlr")
    expected_evlr.record_data = b"Test 1 2 ... 1 2"

    assert len(las.evlrs) == 1
    evlr = las.evlrs[0]
    assert evlr.description == expected_evlr.description
    assert evlr.record_id == expected_evlr.record_id
    assert evlr.user_id == expected_evlr.user_id
    assert evlr.record_data == expected_evlr.record_data


@pytest.mark.skipif(not pylas.LazBackend.Lazrs.is_available(), reason="Lazrs is not installed")
def test_append_laz_with_evlrs():
    las = append_self_and_check(os.path.dirname(__file__) + "/1_4_w_evlr.laz")

    expected_evlr = pylas.EVLR(user_id="pylastest", record_id=42, description="just a test evlr")
    expected_evlr.record_data = b"Test 1 2 ... 1 2"

    assert len(las.evlrs) == 1
    evlr = las.evlrs[0]
    assert evlr.description == expected_evlr.description
    assert evlr.record_id == expected_evlr.record_id
    assert evlr.user_id == expected_evlr.user_id
    assert evlr.record_data == expected_evlr.record_data


def append_self_and_check(las_path_fixture):
    with open(las_path_fixture, mode="rb") as f:
        file = io.BytesIO(f.read())
    las = pylas.read(las_path_fixture)
    with pylas.open(file, mode='a', closefd=False) as laz_file:
        laz_file.append_points(las.points)
    file.seek(0, io.SEEK_SET)
    rlas = pylas.read(file)
    assert rlas.header.point_count == 2 * las.header.point_count
    assert rlas.points[:rlas.header.point_count // 2] == las.points
    assert rlas.points[rlas.header.point_count // 2:] == las.points

    return rlas
