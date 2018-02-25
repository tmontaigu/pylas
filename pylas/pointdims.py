import numpy as np

from . import errors
from collections import namedtuple


# TODO Get rid of the duplication in de dimensions dict
# when building dtype here ?
def point_format_to_dtype(point_format, dimensions):
    return np.dtype([dimensions[dim_name] for dim_name in point_format])


def unpack(source_array, mask):
    lsb = least_significant_bit(mask)
    return (source_array & mask) >> lsb


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


def pack_into(array, array_in, mask, inplace=False):
    lsb = least_significant_bit(mask)
    max_value = int(mask >> lsb)
    if array_in.max() > max_value:
        raise OverflowError("value ({}) is greater than allowed (max: {})".format(
            array_in.max(), max_value
        ))
    if inplace:
        array[:] = (array | mask) & ((array_in << lsb) & mask).astype(array.dtype)
    else:
        return (array | mask) & ((array_in << lsb) & mask).astype(array.dtype)


def least_significant_bit(val):
    return (val & -val).bit_length() - 1


# We use dict for the points_dimensions because not all point formats are supported
# so if we used a list/tuple the indexing would be wrong


# Definition of the points dimensions and formats
# for the point format 0 to 5
# LAS version [1.0, 1.1, 1.2, 1.3]
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

    # Las 1.4
    'bit_fields_1.4': ('bit_fields_1.4', 'u1'),
    'classification_flags': ('classification_flags', 'u1'),
    'scan_angle': ('scan_angle_rank', 'i2'),
    'classification': ('classification', 'u1'),
    'nir': ('nir', 'u2')

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

point_formats_dimensions = {
    0: point_format_0,
    1: point_format_0 + ('gps_time',),
    2: point_format_0 + ('red', 'green', 'blue',),
    3: point_format_0 + ('gps_time', 'red', 'green', 'blue'),
}

# sub fields of the 'bit_fields' dimension
RETURN_NUMBER_MASK = 0b00000111
NUMBER_OF_RETURNS_MASK = 0b00111000
SCAN_DIRECTION_FLAG_MASK = 0b01000000
EDGE_OF_FLIGHT_LINE_MASK = 0b10000000

# sub fields of the 'raw_classification' dimension
CLASSIFICATION_MASK = 0b00011111
SYNTHETIC_MASK = 0b00100000
KEY_POINT_MASK = 0b01000000
WITHHELD_MASK = 0b10000000

point_formats_dtype_base = {fmt_id: point_format_to_dtype(point_fmt, dimensions)
                            for fmt_id, point_fmt in point_formats_dimensions.items()}

# Definition of the points dimensions and formats
# for the point format 6 to 10
# LAS version [1.4]
# Changes are : gps_time mandatory, classification takes full byte,
# some fields take more bytes, some fields re-ordering
point_formats_6 = (
    'X',
    'Y',
    'Z',
    'intensity',
    'bit_fields_1.4',
    'classification_flags',
    'classification',
    'user_data',
    'scan_angle',
    'point_source_id',
    'gps_time'
)

point_formats_dimensions_1_4 = {
    6: point_formats_6,
    7: point_formats_6 + ('red', 'green', 'blue'),
    8: point_formats_6 + ('red', 'green', 'blue', 'nir'),
}

# sub fields of the bit_fields
RETURN_NUMBER_MASK_1_4 = 0b00001111
NUMBER_OF_RETURNS_MASK_1_4 = 0b11110000

# sub fields of classification flags
CLASSIFICATION_FLAGS_MASK = 0b00001111
SCANNER_CHANNEL_MASK = 0b00110000
SCAN_DIRECTION_FLAG_MASK_1_4 = 0b01000000
EDGE_OF_FLIGHT_LINE_MASK_1_4 = 0b10000000

point_formats_dtype_1_4 = {fmt_id: point_format_to_dtype(point_fmt, dimensions)
                           for fmt_id, point_fmt in point_formats_dimensions_1_4.items()}

all_point_formats = {**point_formats_dtype_base, **point_formats_dtype_1_4}

SubField = namedtuple('SubField', ('name', 'mask', 'type'))
sub_fields_dtype_base = {
    'bit_fields': [
        SubField('return_number', RETURN_NUMBER_MASK, 'u1'),
        SubField('number_of_returns', NUMBER_OF_RETURNS_MASK, 'u1'),
        SubField('scan_direction_flag', SCAN_DIRECTION_FLAG_MASK, 'bool'),
        SubField('edge_of_flight_line', EDGE_OF_FLIGHT_LINE_MASK, 'bool'),
    ],
    'raw_classification': [
        SubField('classification', CLASSIFICATION_MASK, 'u1'),
        SubField('synthetic', SYNTHETIC_MASK, 'bool'),
        SubField('key_point', KEY_POINT_MASK, 'bool'),
        SubField('withheld', WITHHELD_MASK, 'bool'),
    ],
    'bit_fields_1.4': [
        SubField('return_number', RETURN_NUMBER_MASK_1_4, 'u1'),
        SubField('number_of_returns', NUMBER_OF_RETURNS_MASK_1_4, 'u1')
    ]
}

all_point_formats_dimensions = {**point_formats_dimensions, **point_formats_dimensions_1_4}

import itertools
unpacked_point_fmt__dtype_base = {}
for fmt_id, point_fmt in itertools.chain(point_formats_dimensions.items(), point_formats_dimensions_1_4.items()):
    dim_names = all_point_formats_dimensions[fmt_id]
    dtype = []
    for dim_name in dim_names:
        if dim_name in sub_fields_dtype_base:
            sub_fields_dtype = [(f.name, f.type) for f in sub_fields_dtype_base[dim_name]]
            dtype.extend(sub_fields_dtype)
        else:
            dtype.append(dimensions[dim_name])

    unpacked_point_fmt__dtype_base[fmt_id] = np.dtype(dtype)
def dtype_append(dtype, extra_dims_tuples):
    descr = dtype.descr
    descr.extend(extra_dims_tuples)
    return np.dtype(descr)


def size_of_point_format(point_format_id):
    return get_dtype_of_format_id(point_format_id).itemsize


# TODO maybe the dtype construction for point formats should be delayed
# and only construct the list that will be used to construct the dtype
def get_dtype_of_format_id(point_format_id, extra_dims=None):
    try:
        points_dtype = all_point_formats[point_format_id]
    except KeyError:
        raise errors.PointFormatNotSupported(point_format_id)
    if extra_dims is not None:
        return dtype_append(points_dtype, extra_dims)
    return points_dtype


def np_dtype_to_point_format(dtype):
    for format_id in all_point_formats:
        fmt_dtype = get_dtype_of_format_id(format_id)
        if fmt_dtype == dtype:
            return format_id
    else:
        raise errors.IncompatibleDataFormat(
            'Data type of array is not compatible with any point format (array dtype: {})'.format(
                dtype
            ))
