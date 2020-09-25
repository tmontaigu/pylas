import pytest

import pylas
from pylas import PointFormat
from pylastests.test_common import extra_bytes_laz


@pytest.mark.skipif(
    len(pylas.LazBackend.detect_available()) == 0, reason="No Laz Backend installed"
)
def test_extra_dims_not_equal():
    """Test to confirm that two point format with same id but
    not same extra dimension are not equal
    """
    las = pylas.read(extra_bytes_laz)
    i = las.points.point_format.id
    assert las.points.point_format != PointFormat(i)
