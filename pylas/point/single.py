import ctypes

from . import dims

DIM_TYPE_TO_CTYPES = {
    'u1': ctypes.c_uint8,
    'u2': ctypes.c_uint16,
    'u4': ctypes.c_uint32,
    'u8': ctypes.c_uint64,
    'i1': ctypes.c_int8,
    'i2': ctypes.c_int16,
    'i4': ctypes.c_int32,
    'i8': ctypes.c_int64,
    'f4': ctypes.c_float,
    'f8': ctypes.c_double
}


def _build_point_fmt_to_ctypes_fields(fmt_dimensions_names, dimension_dict, to_ctypes):
    fields = []
    for _name in fmt_dimensions_names:
        name, dim_type = dimension_dict[_name]
        fields.append((name, to_ctypes[dim_type]))
    return fields


PACKED_FIELDS = {}
for fmt_id, dimensions_names in dims.POINT_FORMAT_DIMENSIONS.items():
    fmt_fields = _build_point_fmt_to_ctypes_fields(
        dimensions_names,
        dims.DIMENSIONS,
        DIM_TYPE_TO_CTYPES
    )
    PACKED_FIELDS[fmt_id] = fmt_fields

PackedPointTypes = {}
for fmt_id, fields in PACKED_FIELDS.items():
    PackedPointTypes[fmt_id] = type(
        "Point{}".format(str(fmt_id).replace('.', '_')),
        (ctypes.LittleEndianStructure,),
        {
            '_pack_': 1,
            '_fields_': fields
        }
    )
