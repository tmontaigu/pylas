from collections import namedtuple

import numpy as np

from . import errors


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
        array[:] = array | ((array_in << lsb) & mask).astype(array.dtype)
    else:
        return array | ((array_in << lsb) & mask).astype(array.dtype)


def least_significant_bit(val):
    return (val & -val).bit_length() - 1


def size_of_point_format(point_format_id):
    return get_dtype_of_format_id(point_format_id).itemsize


def dtype_append(dtype, extra_dims_tuples):
    descr = dtype.descr
    descr.extend(extra_dims_tuples)
    return np.dtype(descr)


# We use dict for the points_dimensions because not all point formats are supported
# so if we used a list/tuple the indexing would be wrong


# Definition of the points dimensions and formats
# for the point format 0 to 5
# LAS version [1.0, 1.1, 1.2, 1.3, 1.4]
DIMENSIONS = {
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

POINT_FORMAT_0 = (
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

POINT_FORMAT_6 = (
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

POINT_FORMAT_DIMENSIONS = {
    0: POINT_FORMAT_0,
    1: POINT_FORMAT_0 + ('gps_time',),
    2: POINT_FORMAT_0 + ('red', 'green', 'blue',),
    3: POINT_FORMAT_0 + ('gps_time', 'red', 'green', 'blue'),
    6: POINT_FORMAT_6,
    7: POINT_FORMAT_6 + ('red', 'green', 'blue'),
    8: POINT_FORMAT_6 + ('red', 'green', 'blue', 'nir'),
}

POINT_FORMATS_DTYPE = {fmt_id: point_format_to_dtype(point_fmt, DIMENSIONS)
                       for fmt_id, point_fmt in POINT_FORMAT_DIMENSIONS.items()}

ALL_POINT_FORMATS_DTYPE = {**POINT_FORMATS_DTYPE}
ALL_POINT_FORMATS_DIMENSIONS = {**POINT_FORMAT_DIMENSIONS}

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


# sub fields of the bit_fields
RETURN_NUMBER_MASK_1_4 = 0b00001111
NUMBER_OF_RETURNS_MASK_1_4 = 0b11110000

# sub fields of classification flags
CLASSIFICATION_FLAGS_MASK = 0b00001111

SYNTHETIC_MASK_1_4 = 0b00000001
KEY_POINT_MASK_1_4 = 0b00000010
WITHHELD_MASK_1_4 = 0b00000100
OVERLAP_MASK_1_4 = 0b00001000
SCANNER_CHANNEL_MASK_1_4 = 0b00110000
SCAN_DIRECTION_FLAG_MASK_1_4 = 0b01000000
EDGE_OF_FLIGHT_LINE_MASK_1_4 = 0b10000000

SubField = namedtuple('SubField', ('name', 'mask', 'type'))
SUB_FIELDS = {
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
        SubField('number_of_returns', NUMBER_OF_RETURNS_MASK_1_4, 'u1'),
    ],
    'classification_flags': [
        SubField('synthetic', SYNTHETIC_MASK_1_4, 'bool'),
        SubField('key_point', KEY_POINT_MASK_1_4, 'bool'),
        SubField('withheld', WITHHELD_MASK_1_4, 'bool'),
        SubField('overlap', OVERLAP_MASK_1_4, 'bool'),
        SubField('scanner_channel', SCANNER_CHANNEL_MASK_1_4, 'u1'),
        SubField('scan_direction_flag', SCAN_DIRECTION_FLAG_MASK_1_4, 'bool'),
        SubField('edge_of_flight_line', EDGE_OF_FLIGHT_LINE_MASK_1_4, 'bool'),
    ],
}

UNPACKED_POINT_FORMATS_DTYPES = {}
for fmt_id, point_fmt in POINT_FORMAT_DIMENSIONS.items():
    dim_names = ALL_POINT_FORMATS_DIMENSIONS[fmt_id]
    dtype = []
    for dim_name in dim_names:
        if dim_name in SUB_FIELDS:
            sub_fields_dtype = [(f.name, f.type) for f in SUB_FIELDS[dim_name]]
            dtype.extend(sub_fields_dtype)
        else:
            dtype.append(DIMENSIONS[dim_name])

    UNPACKED_POINT_FORMATS_DTYPES[fmt_id] = np.dtype(dtype)


def get_dtype_of_format_id(point_format_id, extra_dims=None):
    try:
        points_dtype = ALL_POINT_FORMATS_DTYPE[point_format_id]
    except KeyError:
        raise errors.PointFormatNotSupported(point_format_id)
    if extra_dims is not None:
        return dtype_append(points_dtype, extra_dims)
    return points_dtype


def np_dtype_to_point_format(dtype):
    for format_id in ALL_POINT_FORMATS_DTYPE:
        fmt_dtype = get_dtype_of_format_id(format_id)
        if fmt_dtype == dtype:
            return format_id
    else:
        raise errors.IncompatibleDataFormat(
            'Data type of array is not compatible with any point format (array dtype: {})'.format(
                dtype
            ))
