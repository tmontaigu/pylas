""" This module contains functions to pack and unpack point dimensions
"""
import numpy as np

from .dims import get_dtype_of_format_id, COMPOSED_FIELDS, get_extra_dimensions_spec


def least_significant_bit(val):
    """ Return the least significant bit
    """
    return (val & -val).bit_length() - 1


def unpack(source_array, mask, dtype=np.uint8):
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
    return ((source_array & mask) >> lsb).astype(dtype)


def pack(array, sub_field_array, mask, inplace=False):
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
        raise OverflowError(
            "value ({}) is greater than allowed (max: {})".format(
                sub_field_array.max(), max_value
            )
        )
    if inplace:
        array[:] = array & ~mask
        array[:] = array | ((sub_field_array << lsb) & mask).astype(array.dtype)
    else:
        array = array & ~mask
        return array | ((sub_field_array << lsb) & mask).astype(array.dtype)


def unpack_sub_fields(data, point_format_id):
    """ Unpack all the composed fields of the structured_array into their corresponding
    sub-fields

    Returns:
        A new structured array with the sub-fields de-packed
    """
    composed_dims = COMPOSED_FIELDS[point_format_id]
    extra_dims = get_extra_dimensions_spec(data.dtype, point_format_id)
    dtype = get_dtype_of_format_id(point_format_id, extra_dims, unpacked=True)
    point_record = np.zeros_like(data, dtype)

    for dim_name in data.dtype.names:
        if dim_name in composed_dims:
            for sub_field in composed_dims[dim_name]:
                point_record[sub_field.name] = unpack(data[dim_name], sub_field.mask)
        else:
            point_record[dim_name] = data[dim_name]
    return point_record


def repack_sub_fields(structured_array, point_format_id):
    """ Repack all the sub-fields of the structured_array into their corresponding
    composed fields

    Returns:
        A new structured array without the de-packed sub-fields
    """
    extra_dims = get_extra_dimensions_spec(structured_array.dtype, point_format_id)
    dtype = get_dtype_of_format_id(point_format_id, extra_dims=extra_dims)
    repacked_array = np.zeros_like(structured_array, dtype)
    composed_dims = COMPOSED_FIELDS[point_format_id]

    for dim_name in repacked_array.dtype.names:
        if dim_name in composed_dims:
            for sub_field in composed_dims[dim_name]:
                try:
                    pack(
                        repacked_array[dim_name],
                        structured_array[sub_field.name],
                        sub_field.mask,
                        inplace=True,
                    )
                except OverflowError as e:
                    raise OverflowError(
                        "Error repacking {} into {}: {}".format(
                            sub_field.name, dim_name, e
                        )
                    )
        else:
            repacked_array[dim_name] = structured_array[dim_name]
    return repacked_array
