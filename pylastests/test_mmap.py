import numpy as np

import pylas


def test_mmap(mmapped_file_path):
    with pylas.mmap(mmapped_file_path) as las:
        las.classification[:] = 25
        assert np.all(las.classification == 25)

    las = pylas.read(mmapped_file_path)
    assert np.all(las.classification == 25)


