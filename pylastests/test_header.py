import pylas
from pylastests import test_common

all_las_but_1_4 = test_common.all_las_but_1_4


def test_number_of_points_return_is_updated(all_las_but_1_4):
    las = all_las_but_1_4

    nb_points = len(las.points_data)
    nb_slice = 3

    r = las.return_number

    for i in reversed(range(nb_slice)):
        r[i * (nb_points // nb_slice) : (i + 1) * (nb_points // nb_slice)] = i

    las.return_number = r
    las = test_common.write_then_read_again(las)

    assert (
        tuple(las.header.number_of_points_by_return[:nb_slice])
        == (nb_points // nb_slice,) * nb_slice
    )
    assert tuple(las.header.number_of_points_by_return[nb_slice:]) == (0,) * (
        len(las.header.number_of_points_by_return) - nb_slice
    )


def test_nb_points_return_1_4():
    las = pylas.read(test_common.test1_4_las)

    r = las.return_number

    for i in reversed(range(15)):
        r[i] = i

    r[14:] = 15

    las.return_number = r
    las = test_common.write_then_read_again(las)

    assert tuple(las.header.number_of_points_by_return) == ((1,) * 14) + (
        len(las.points_data) - 14,
    )


def test_header_copy():
    import copy

    las = pylas.read(test_common.simple_las)
    header_copy = copy.copy(las.header)

    assert header_copy.point_format_id == las.header.point_format_id
    assert header_copy.version == las.header.version

    header_copy.point_format_id = 0
    assert header_copy.point_format_id != las.header.point_format_id
    assert header_copy.version == las.header.version


def test_set_uuid():
    import uuid

    las = pylas.read(test_common.simple_las)
    u = uuid.uuid4()
    las.header.uuid = u
    las = test_common.write_then_read_again(las)
    assert las.header.uuid == u
