from collections import namedtuple

import numpy as np

from pylas import errors


def least_significant_bit(val):
    """ Return the least significant bit
    """
    return (val & -val).bit_length() - 1


def unpack(source_array, mask):
    """ Unpack sub field using its mask
    
    Parameters:
    ----------
    source_array : numpy.ndarray
        The source array
    mask : mask (ie: 0b00001111)
        Mask of the sub field to be extracted from the source array
    Returns
    -------
    numpy.ndarray
        The sub field array
    """
    lsb = least_significant_bit(mask)
    return (source_array & mask) >> lsb


def pack_into(array, sub_field_array, mask, inplace=False):
    """ Packs a sub field's array into another array using a mask
    
    Parameters:
    ----------
    array : numpy.ndarray 
        The array in which the sub field array will be packed into
    array_in : numpy.ndarray
        sub field array to pack
    mask : mask (ie: 0b00001111)
        Mask of the sub field
    inplace : {bool}, optional
        If true a new array is returned. (the default is False, which modifies the array in place)
    
    Raises
    ------
    OverflowError
        If the values contained in the sub field array are greater than its mask's number of bits
        allows
    """
    lsb = least_significant_bit(mask)
    max_value = int(mask >> lsb)
    if sub_field_array.max() > max_value:
        raise OverflowError("value ({}) is greater than allowed (max: {})".format(
            sub_field_array.max(), max_value
        ))
    if inplace:
        array[:] = array & ~mask
        array[:] = array | ((sub_field_array << lsb) & mask).astype(array.dtype)
    else:
        array = array & ~mask
        return array | ((sub_field_array << lsb) & mask).astype(array.dtype)


def point_format_to_dtype(point_format, dimensions):
    """ build the numpy.dtype for a point format
    
    Parameters:
    ----------
    point_format : tuple of str
        The dimensions names of the point format
    dimensions : dict
        The dictionnary of dimensions
    Returns
    -------
    numpy.dtype
        The dtype for the input point format
    """
    return np.dtype([dimensions[dim_name] for dim_name in point_format])


def size_of_point_format(point_format_id):
    """ Returns the size in bytes of a point format
    """
    return get_dtype_of_format_id(point_format_id).itemsize


def dtype_append(dtype, extra_dims_tuples):
    """ Append a dimensions to an existing dtype
    """
    descr = dtype.descr
    descr.extend(extra_dims_tuples)
    return np.dtype(descr)


def build_point_formats_dtypes(point_format_dimensions, dimensions_dict):
    return {fmt_id: point_format_to_dtype(point_fmt, dimensions_dict)
            for fmt_id, point_fmt in point_format_dimensions.items()}


def build_unpacked_point_formats_dtypes(point_formats_dimensions, composed_fields_dict, dimensions_dict):
    unpacked_dtypes = {}
    for fmt_id, dim_names in point_formats_dimensions.items():
        composed_dims, dtype = composed_fields_dict[fmt_id], []
        for dim_name in dim_names:
            if dim_name in composed_dims:
                dtype.extend((f.name, f.type) for f in composed_dims[dim_name])
            else:
                dtype.append(dimensions_dict[dim_name])
        unpacked_dtypes[fmt_id] = np.dtype(dtype)
    return unpacked_dtypes


# Definition of the points dimensions and formats
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
    'bit_fields',
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

# sub fields of the 'bit_fields' dimension
RETURN_NUMBER_MASK_0 = 0b00000111
NUMBER_OF_RETURNS_MASK_0 = 0b00111000
SCAN_DIRECTION_FLAG_MASK_0 = 0b01000000
EDGE_OF_FLIGHT_LINE_MASK_0 = 0b10000000

# sub fields of the 'raw_classification' dimension
CLASSIFICATION_MASK_0 = 0b00011111
SYNTHETIC_MASK_0 = 0b00100000
KEY_POINT_MASK_0 = 0b01000000
WITHHELD_MASK_0 = 0b10000000

# sub fields of the bit_fields
RETURN_NUMBER_MASK_6 = 0b00001111
NUMBER_OF_RETURNS_MASK_6 = 0b11110000

# sub fields of classification flags
CLASSIFICATION_FLAGS_MASK_6 = 0b00001111

SYNTHETIC_MASK_6 = 0b00000001
KEY_POINT_MASK_6 = 0b00000010
WITHHELD_MASK_6 = 0b00000100
OVERLAP_MASK_6 = 0b00001000
SCANNER_CHANNEL_MASK_6 = 0b00110000
SCAN_DIRECTION_FLAG_MASK_6 = 0b01000000
EDGE_OF_FLIGHT_LINE_MASK_6 = 0b10000000

SubField = namedtuple('SubField', ('name', 'mask', 'type'))
COMPOSED_FIELDS_0 = {
    'bit_fields': [
        SubField('return_number', RETURN_NUMBER_MASK_0, 'u1'),
        SubField('number_of_returns', NUMBER_OF_RETURNS_MASK_0, 'u1'),
        SubField('scan_direction_flag', SCAN_DIRECTION_FLAG_MASK_0, 'bool'),
        SubField('edge_of_flight_line', EDGE_OF_FLIGHT_LINE_MASK_0, 'bool'),
    ],
    'raw_classification': [
        SubField('classification', CLASSIFICATION_MASK_0, 'u1'),
        SubField('synthetic', SYNTHETIC_MASK_0, 'bool'),
        SubField('key_point', KEY_POINT_MASK_0, 'bool'),
        SubField('withheld', WITHHELD_MASK_0, 'bool'),
    ],
}
COMPOSED_FIELDS_6 = {
    'bit_fields': [
        SubField('return_number', RETURN_NUMBER_MASK_6, 'u1'),
        SubField('number_of_returns', NUMBER_OF_RETURNS_MASK_6, 'u1'),
    ],
    'classification_flags': [
        SubField('synthetic', SYNTHETIC_MASK_6, 'bool'),
        SubField('key_point', KEY_POINT_MASK_6, 'bool'),
        SubField('withheld', WITHHELD_MASK_6, 'bool'),
        SubField('overlap', OVERLAP_MASK_6, 'bool'),
        SubField('scanner_channel', SCANNER_CHANNEL_MASK_6, 'u1'),
        SubField('scan_direction_flag', SCAN_DIRECTION_FLAG_MASK_6, 'bool'),
        SubField('edge_of_flight_line', EDGE_OF_FLIGHT_LINE_MASK_6, 'bool'),
    ],
}

COMPOSED_FIELDS = {
    0: COMPOSED_FIELDS_0,
    1: COMPOSED_FIELDS_0,
    2: COMPOSED_FIELDS_0,
    3: COMPOSED_FIELDS_0,
    6: COMPOSED_FIELDS_6,
    7: COMPOSED_FIELDS_6,
    8: COMPOSED_FIELDS_6,
}

VERSION_TO_POINT_FMT = {
    '1.2': (0, 1, 2, 3),
    '1.3': (0, 1, 2, 3, 4, 5),
    '1.4': (0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10)
}

POINT_FORMATS_DTYPE = build_point_formats_dtypes(POINT_FORMAT_DIMENSIONS, DIMENSIONS)

ALL_POINT_FORMATS_DIMENSIONS = {**POINT_FORMAT_DIMENSIONS}
ALL_POINT_FORMATS_DTYPE = {**POINT_FORMATS_DTYPE}

UNPACKED_POINT_FORMATS_DTYPES = build_unpacked_point_formats_dtypes(
    POINT_FORMAT_DIMENSIONS, COMPOSED_FIELDS, DIMENSIONS)


def unpack_sub_fields(data, point_format_id, extra_dims=None):
    dtype = get_dtype_of_format_id(point_format_id, extra_dims=extra_dims, unpacked=True)
    composed_dims = COMPOSED_FIELDS[point_format_id]
    point_record = np.zeros_like(data, dtype)

    for dim_name in data.dtype.names:
        if dim_name in composed_dims:
            for sub_field in composed_dims[dim_name]:
                point_record[sub_field.name] = unpack(data[dim_name], sub_field.mask)
        else:
            point_record[dim_name] = data[dim_name]
    return point_record


def repack_sub_fields(data, point_format_id):
    repacked_array = np.zeros_like(data, get_dtype_of_format_id(point_format_id))
    composed_dims = COMPOSED_FIELDS[point_format_id]

    for dim_name in repacked_array.dtype.names:
        if dim_name in composed_dims:
            for sub_field in composed_dims[dim_name]:
                try:
                    pack_into(
                        repacked_array[dim_name],
                        data[sub_field.name],
                        sub_field.mask,
                        inplace=True
                    )
                except OverflowError as e:
                    raise OverflowError("Error repacking {} into {}: {}".format(sub_field.name, dim_name, e))
        else:
            repacked_array[dim_name] = data[dim_name]
    return repacked_array


def get_dtype_of_format_id(point_format_id, extra_dims=None, unpacked=False):
    fmt_dtypes = ALL_POINT_FORMATS_DTYPE if not unpacked else UNPACKED_POINT_FORMATS_DTYPES
    try:
        points_dtype = fmt_dtypes[point_format_id]
    except KeyError:
        raise errors.PointFormatNotSupported(point_format_id)
    if extra_dims is not None:
        return dtype_append(points_dtype, extra_dims)
    return points_dtype


def get_sub_fields_of_fmt_id(point_format_id):
    composed_dims = COMPOSED_FIELDS[point_format_id]
    sub_fields_dict = {}
    for composed_dim_name, sub_fields in composed_dims.items():
        for sub_field in sub_fields:
            sub_fields_dict[sub_field.name] = (composed_dim_name, sub_field)
    return sub_fields_dict


def np_dtype_to_point_format(dtype, unpacked=False):
    """ Tries to find a matching point format id for the input numpy dtype
    To match, the input dtype has to be 100% equal to a point format dtype
    so all names & dimensions types must match

    Parameters:
    ----------
    dtype : numpy.dtype
        The input dtype
    unpacked : {bool}, optional
        [description] (the default is False, which [default_description])
    
    Raises
    ------
    errors.IncompatibleDataFormat
        If No compatible point format was found
    
    Returns
    -------
    int
        The compatible point format found
    """

    all_dtypes = ALL_POINT_FORMATS_DTYPE if not unpacked else UNPACKED_POINT_FORMATS_DTYPES
    for format_id, fmt_dtype in all_dtypes.items():
        if fmt_dtype == dtype:
            return format_id
    else:
        raise errors.IncompatibleDataFormat(
            'Data type of array is not compatible with any point format (array dtype: {})'.format(
                dtype
            ))


def min_file_version_for_point_format(point_format_id):
    for version, point_formats in sorted(VERSION_TO_POINT_FMT.items()):
        if point_format_id in point_formats:
            return version
    else:
        raise errors.PointFormatNotSupported(point_format_id)
