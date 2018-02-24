import pytest
import pylas
import numpy as np
import io

@pytest.fixture()
def file():
    return pylas.open('simple.las')

def test_extraction(file):
    new = pylas.create_las(point_format=0)

    assert file.points_data.point_format_id == 3

    # automatic promotion of point format
    new.points = file.points[file.classification == 2]
    assert new.points_data.point_format_id == 3

    assert len(new.points) == sum(file.classification == 2)
    assert np.all(new.classification == 2)

    out = io.BytesIO()

    new.write(out)
    out.seek(0)

    file = pylas.open(out)
    assert all(file.classification == 2)


