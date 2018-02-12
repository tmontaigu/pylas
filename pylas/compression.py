from .pointdimensions import point_formats
from .errors import PointFormatNotSupported, LazPerfNotFound
import numpy as np
import json

HAS_LAZPERF = False

try:
    import lazperf

    HAS_LAZPERF = True
except ModuleNotFoundError:
    HAS_LAZPERF = False

def raise_if_not_lazperf():
    if not HAS_LAZPERF:
        raise LazPerfNotFound('Lazperf not found, cannot manipulate laz data')


DIMENSIONS_SCHEMA = {
    'X': {u'type': u'signed', u'name': u'X', u'size': 4},
    'Y': {u'type': u'signed', u'name': u'Y', u'size': 4},
    'Z': {u'type': u'signed', u'name': u'Z', u'size': 4},
    'intensity': {u'type': u'unsigned', u'name': u'intensity', u'size': 2},
    'bit_fields': {u'type': u'unsigned', u'name': u'bit_fields', u'size': 1},
    'raw_classification': {u'type': u'unsigned', u'name': u'raw_classification', u'size': 1},
    'scan_angle_rank': {u'type': u'signed', u'name': u'scan_angle_rank', u'size': 1},
    'user_data': {u'type': u'unsigned', u'name': u'user_data', u'size': 1},
    'point_source_id': {u'type': u'unsigned', u'name': u'point_source_id', u'size': 2},
    'gps_time': {u'type': u'floating', u'name': u'gps_time', u'size': 8},
    'red': {u'type': u'unsigned', u'name': u'red', u'size': 2},
    'green': {u'type': u'unsigned', u'name': u'green', u'size': 2},
    'blue': {u'type': u'unsigned', u'name': u'blue', u'size': 2},
}

point_dimensions_schemas = []
for point_format in point_formats:
    point_schema = [DIMENSIONS_SCHEMA[dim_name] for dim_name in point_format]
    point_dimensions_schemas.append(point_schema)


def is_point_format_compressed(point_format_id):
    try:
        compression_bit_7 = (point_format_id & 0x80) >> 7
        compression_bit_6 = (point_format_id & 0x40) >> 6
        if not compression_bit_6 and compression_bit_7:
            return True
    except ValueError:
        pass
    return False

def compressed_id_to_uncompressed(point_format_id):
    return (point_format_id & 0x3f)

def get_schema_of_point_format_id(point_format_id):
    try:
        schema = point_dimensions_schemas[point_format_id]
    except IndexError:
        raise PointFormatNotSupported(point_format_id)

    return schema

def decompress_stream(compressed_stream, point_format_id, point_count):
    raise_if_not_lazperf()
    schema = get_schema_of_point_format_id(point_format_id)
    ndtype = lazperf.buildNumpyDescription(schema)

    buffer = compressed_stream.read(point_count * ndtype.itemsize)

    arr = np.frombuffer(buffer, dtype=np.uint8)
    d = lazperf.Decompressor(arr, json.dumps(schema))
    output = np.zeros(point_count * ndtype.itemsize, dtype=np.uint8)

    return d.decompress(output)




