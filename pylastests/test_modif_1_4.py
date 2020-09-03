import numpy as np
import pytest

import pylas
from pylas import LazBackend
from pylas.errors import PylasError
from pylastests.test_common import test1_4_las, write_then_read_again


@pytest.fixture(scope="session")
def las():
    return pylas.read(test1_4_las)


@pytest.fixture(params=LazBackend.detect_available())
def laz_backend(request):
    return request.param


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


def test_writing_las_with_evlrs():
    las = pylas.read(test1_4_las)
    assert las.evlrs == []

    evlr = pylas.EVLR(user_id="pylastest", record_id=42, description="Just a test")
    evlr.record_data = b"And so he grinds his own hands"
    las.evlrs.append(evlr)

    las_1 = write_then_read_again(las, do_compress=False)
    assert las_1.evlrs == [evlr]


@pytest.mark.skip(reason="Writing LAZ with EVLRs is not well supported")
def test_writing_laz_with_evlrs(laz_backend):
    las = pylas.read(test1_4_las)
    assert las.evlrs == []

    evlr = pylas.EVLR(user_id="pylastest", record_id=42, description="Just a test")
    evlr.record_data = b"And so he grinds his own hands"
    las.evlrs.append(evlr)

    if laz_backend == LazBackend.Laszip:
        with pytest.raises(PylasError) as exc_info:
            las_1 = write_then_read_again(
                las, do_compress=True, laz_backend=(laz_backend,)
            )
        assert (
            "Reading a LAZ file that contains EVLR using laszip is not supported"
            in exc_info.value
        )
    else:
        las_1 = write_then_read_again(las, do_compress=True, laz_backend=(laz_backend,))
        assert las_1.evlrs == [evlr]
