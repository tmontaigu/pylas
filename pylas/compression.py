import numpy as np

from .errors import LazPerfNotFound
from .pointdimensions import get_dtype_of_format_id

HAS_LAZPERF = False

try:
    import lazperf

    HAS_LAZPERF = True
except ModuleNotFoundError:
    HAS_LAZPERF = False


def raise_if_no_lazperf():
    if not HAS_LAZPERF:
        raise LazPerfNotFound('Lazperf not found, cannot manipulate laz data')


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
    return point_format_id & 0x3f


def decompress_stream(compressed_stream, point_format_id, point_count, laszip_vlr):
    raise_if_no_lazperf()

    ndtype = get_dtype_of_format_id(point_format_id)
    point_compressed = np.frombuffer(compressed_stream.read(), dtype=np.uint8)
    point_uncompressed = np.zeros(point_count, dtype=ndtype)

    vlr_data = np.frombuffer(laszip_vlr.record_data, dtype=np.uint8)
    decompressor = lazperf.VLRDecompressor(point_compressed, vlr_data)
    point_buffer = np.zeros((ndtype.itemsize,))

    begin = 0
    for i in range(point_count):
        decompressor.decompress(point_buffer)
        end = begin + ndtype.itemsize
        point = np.frombuffer(point_buffer, dtype=ndtype)[0]
        point_uncompressed[i] = point
        begin = end

    return point_uncompressed
