import pylas
from pylastests import test_common

all_las_but_1_4 = test_common.all_las_but_1_4


def test_number_of_points_return_is_updated(all_las_but_1_4):
    las = all_las_but_1_4

    nb_points = len(las.points)
    nb_slice = 3

    r = las.return_number

    for i in reversed(range(nb_slice)):
        r[i * (nb_points // nb_slice) : (i + 1) * (nb_points // nb_slice)] = i + 1

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

    for i in range(15):
        r[i] = i + 1

    r[15:] = 15

    las = test_common.write_then_read_again(las)

    assert tuple(las.header.number_of_points_by_return) == ((1,) * 14) + (
        len(las.points) - 14,
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


def test_set_offsets():
    header = pylas.headers.HeaderFactory.new("1.2")
    header.offsets = [0.5, 0.6, 0.7]

    assert 0.5 == header.x_offset
    assert 0.6 == header.y_offset
    assert 0.7 == header.z_offset
    assert [0.5, 0.6, 0.7] == list(header.offsets)


def test_set_scales():
    header = pylas.headers.HeaderFactory.new("1.2")
    header.scales = [0.001, 0.001, 0.01]

    assert 0.001 == header.x_scale
    assert 0.001 == header.y_scale
    assert 0.01 == header.z_scale
    assert [0.001, 0.001, 0.01] == list(header.scales)


def test_set_maxs():
    header = pylas.headers.HeaderFactory.new("1.2")
    values = [42.0, 1337.42, 553.3]
    header.maxs = values

    assert values[0] == header.x_max
    assert values[1] == header.y_max
    assert values[2] == header.z_max
    assert values == list(header.maxs)


def test_set_mins():
    header = pylas.headers.HeaderFactory.new("1.2")
    values = [42.0, 1337.42, 553.3]
    header.mins = values

    assert values[0] == header.x_min
    assert values[1] == header.y_min
    assert values[2] == header.z_min
    assert values == list(header.mins)


def test_point_count_stays_synchronized():
    las = pylas.read(test_common.simple_las)
    assert las.header.point_count == len(las.points)

    las.points = las.points[:120]
    assert 120 == las.header.point_count
    assert las.header.point_count == len(las.points)
