import ctypes
import struct

from collections import namedtuple
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

DIM_TYPE_TO_STRUCT_TYPE = {
    'u1': 'B',
    'u2': 'H',
    'u4': 'I',
    'u8': 'L',
    'i1': 'b',
    'i2': 'h',
    'i4': 'i',
    'i8': 'L',
    'f4': 'f',
    'f8': 'd',
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
            '_fields_': fields,
            '__slots__': [f[0] for f in fields]
        }
    )

StructStrings = {}
StructSizes = {}
ptuples = {}

for fmt_id, fields in dims.POINT_FORMAT_DIMENSIONS.items():
    ptuples[fmt_id] = namedtuple(f'PointTuple{fmt_id}', tuple(fields))
    fields_type = [dims.DIMENSIONS[name][1] for name in fields]
    StructStrings[fmt_id] = '<' + ''.join(DIM_TYPE_TO_STRUCT_TYPE[t] for t in fields_type)
    StructSizes[fmt_id] = struct.calcsize(StructStrings[fmt_id])

