from . import errors
from .point.dims import DimensionKind

_extra_dims_base_style_1 = (
    "",
    "u1",
    "i1",
    "u2",
    "i2",
    "u4",
    "i4",
    "u8",
    "i8",
    "f4",
    "f8",
)
_extra_dims_base_style_2 = (
    "",
    "uint8",
    "int8",
    "uint16",
    "int16",
    "uint32",
    "int32",
    "uint64",
    "int64",
    "float32",
    "float64",
)

_extra_dims_style_1_array_2 = tuple(
    "2{}".format(_type) for _type in _extra_dims_base_style_1[1:]
)
_extra_dims_style_1_array_3 = tuple(
    "3{}".format(_type) for _type in _extra_dims_base_style_1[1:]
)

_extra_dims_style_2_array_2 = tuple(
    "2{}".format(_type) for _type in _extra_dims_base_style_2[1:]
)
_extra_dims_style_2_array_3 = tuple(
    "3{}".format(_type) for _type in _extra_dims_base_style_2[1:]
)

_extra_dims_style_1 = (
    _extra_dims_base_style_1 + _extra_dims_style_1_array_2 + _extra_dims_style_1_array_3
)
_extra_dims_style_2 = (
    _extra_dims_base_style_2 + _extra_dims_style_1_array_2 + _extra_dims_style_2_array_3
)

_type_to_extra_dim_id_style_1 = {
    type_str: i for i, type_str in enumerate(_extra_dims_style_1)
}
_type_to_extra_dim_id_style_2 = {
    type_str: i for i, type_str in enumerate(_extra_dims_style_2)
}


def get_kind_of_extra_dim(type_index: int) -> DimensionKind:
    """Returns the signedness foe the given type index

    Parameters
    ----------
    type_index: int
        index of the type as defined in the LAS Specification

    Returns
    -------
    DimensionSignedness,
        the enum variant
    """
    try:
        t = _extra_dims_style_2[type_index]
        if "uint" in t:
            return DimensionKind.UnsignedInteger
        elif "int" in t:
            return DimensionKind.SignedInteger
        else:
            return DimensionKind.FloatingPoint
    except IndexError:
        raise errors.UnknownExtraType(type_index)


def get_type_for_extra_dim(type_index: int) -> str:
    """Returns the type str ('u1" or "u2", etc) for the given type index
    Parameters
    ----------
    type_index: int
        index of the type as defined in the LAS Specification

    Returns
    -------
    str,
        a string representing the type, can be understood by numpy

    """
    try:
        return _extra_dims_style_1[type_index]
    except IndexError:
        raise errors.UnknownExtraType(type_index)


def get_id_for_extra_dim_type(type_str: str) -> int:
    """Returns the index of the type as defined in the LAS Specification

    Parameters
    ----------
    type_str: str

    Returns
    -------
    int
        index of the type

    """
    try:
        return _type_to_extra_dim_id_style_1[type_str]
    except KeyError:
        try:
            return _type_to_extra_dim_id_style_2[type_str]
        except KeyError:
            raise errors.UnknownExtraType(type_str) from None
