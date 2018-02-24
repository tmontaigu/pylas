import pylas
import pytest
import numpy as np
import io

def test_incompatible_data_type():
    las = pylas.create_las()
    dtype = np.dtype([('X', 'u4'), ('Y', 'u4'), ('Z', 'u4'), ('codification', 'u4'), ('intensity', 'i2')])
    with pytest.raises(pylas.errors.IncompatibleDataFormat):
        las.points = np.zeros(120, dtype=dtype)


def test_xyz():
    las = pylas.create_las()
    shape = (150,)
    las.X = np.zeros(shape, dtype=np.int32)
    las.Y = np.ones(shape, dtype=np.int32)
    las.Z = np.zeros(shape, dtype=np.int32)
    las.Z[:] = -152

    out = io.BytesIO()
    las.write(out)
    out.seek(0)

    las = pylas.open(out)
    assert np.alltrue(las.X == 0)
    assert np.alltrue(las.Y == 1)
    assert np.alltrue(las.Z == -152)


