import numpy as np

from pylastests.test_common import las

las = las


def test_unpacking(las):
    packed_points = las.points_data
    unpacked_points = packed_points.to_unpacked()

    assert packed_points.point_format.dimension_names == unpacked_points.point_format.dimension_names
    for dim_name in unpacked_points.point_format.dimension_names:
        assert np.allclose(packed_points[dim_name], unpacked_points[dim_name])


def test_packing(las):
    packed_points = las.points_data
    unpacked_points = packed_points.to_unpacked()
    repacked_points = unpacked_points.to_packed()

    assert packed_points.point_format.dimension_names == repacked_points.point_format.dimension_names
    for dim_name in repacked_points.point_format.dimension_names:
        assert np.allclose(packed_points[dim_name], repacked_points[dim_name])
