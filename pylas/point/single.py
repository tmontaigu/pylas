import struct
from collections import namedtuple

from . import dims

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

StructStrings = {}
StructSizes = {}
PointTupleClasses = {}

for fmt_id, fields_names in dims.POINT_FORMAT_DIMENSIONS.items():
    fields_type = [dims.DIMENSIONS[name][1] for name in fields_names]
    PointTupleClasses[fmt_id] = namedtuple(f'PointTuple{fmt_id}', tuple(fields_names))
    StructStrings[fmt_id] = '<' + ''.join(DIM_TYPE_TO_STRUCT_TYPE[t] for t in fields_type)
    StructSizes[fmt_id] = struct.calcsize(StructStrings[fmt_id])
