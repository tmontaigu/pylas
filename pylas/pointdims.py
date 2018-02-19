import numpy as np

from pylas.errors import PointFormatNotSupported


def point_format_to_dtype(point_format):
    return [dimensions[dim_name] for dim_name in point_format]


def unpack(source_array, mask):
    lsb = least_significant_bit(mask)
    return (source_array & mask) >> lsb


# TODO: The error message could be more useful
# if we somehow knew the dimension that is overflowed

def repack(arrays, masks):
    packed = np.zeros_like(arrays[0])
    for array, mask in zip(arrays, masks):
        lsb = least_significant_bit(mask)
        msb = (mask >> lsb).bit_length()
        max_value = (2 ** msb) - 1
        if array.max() > max_value:
            raise ValueError("value ({}) is greater than allowed (max: {})".format(
                array.max(), max_value
            ))
        packed = packed | ((array << lsb) & mask)
    return packed


def least_significant_bit(val):
    return (val & -val).bit_length() - 1


RETURN_NUMBER_MASK = 0b00000111
NUMBER_OF_RETURNS_MASK = 0b00111000
SCAN_DIRECTION_FLAG_MASK = 0b01000000
EDGE_OF_FLIGHT_LINE_MASK = 0b10000000

CLASSIFICATION_MASK = 0b00011111
SYNTHETIC_MASK = 0b00100000
KEY_POINT_MASK = 0b01000000
WITHHELD_MASK = 0b10000000

dimensions = {
    'X': ('X', 'i4'),
    'Y': ('Y', 'i4'),
    'Z': ('Z', 'i4'),
    'intensity': ('intensity', 'u2'),
    'bit_fields': ('bit_fields', 'u1'),
    'raw_classification': ('raw_classification', 'u1'),
    'scan_angle_rank': ('scan_angle_rank', 'i1'),
    'user_data': ('user_data', 'u1'),
    'point_source_id': ('point_source_id', 'u2'),
    'gps_time': ('gps_time', 'f8'),
    'red': ('red', 'u2'),
    'green': ('green', 'u2'),
    'blue': ('blue', 'u2'),
}

point_format_0 = (
    'X',
    'Y',
    'Z',
    'intensity',
    'bit_fields',
    'raw_classification',
    'scan_angle_rank',
    'user_data',
    'point_source_id'
)

point_formats_dimensions = (
    point_format_0,
    point_format_0 + ('gps_time',),
    point_format_0 + ('red', 'green', 'blue',),
    point_format_0 + ('gps_time', 'red', 'green', 'blue'),
)

point_formats_dtype = tuple(np.dtype(point_format_to_dtype(point_fmt)) for point_fmt in point_formats_dimensions)


def get_dtype_of_format_id(point_format_id):
    try:
        points_dtype = point_formats_dtype[point_format_id]
    except IndexError:
        raise PointFormatNotSupported(point_format_id)

    return points_dtype
