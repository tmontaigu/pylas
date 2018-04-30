import struct
from collections import namedtuple
from functools import partial

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


def sub_field_getter(composed_dim_name, mask, self):
    return getattr(self, composed_dim_name) & mask


for fmt_id, fields_names in dims.POINT_FORMAT_DIMENSIONS.items():
    fields_type = [dims.DIMENSIONS[name][1] for name in fields_names]
    PointTupleClasses[fmt_id] = namedtuple(f'PointTuple{fmt_id}', tuple(fields_names))
    StructStrings[fmt_id] = '<' + ''.join(DIM_TYPE_TO_STRUCT_TYPE[t] for t in fields_type)
    StructSizes[fmt_id] = struct.calcsize(StructStrings[fmt_id])
    for composed_dim_name, sub_fields in dims.COMPOSED_FIELDS[fmt_id].items():
        for sub_field in sub_fields:
            setattr(PointTupleClasses[fmt_id], sub_field.name, property(
                partial(sub_field_getter, composed_dim_name, sub_field.mask)
                # No setter for now
            ))
