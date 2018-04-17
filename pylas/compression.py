""" The functions related to the LAZ format (compressed LAS)
Lazperf is made optional by catching the ModuleNotFoundError, and raising an exception
when compression/decompression is actually needed

There are also functions to use Laszip (meant to be used as a fallback)
"""
import os
import subprocess

import numpy as np

from .errors import LazPerfNotFound
from .point.dims import get_dtype_of_format_id, POINT_FORMAT_DIMENSIONS

HAS_LAZPERF = False

try:
    import lazperf

    HAS_LAZPERF = True
    # we should capture ModuleNotRoundError but its python3.6 exception type
    # and ReadTheDocs does uses 3.5
except:
    HAS_LAZPERF = False


def raise_if_no_lazperf():
    if not HAS_LAZPERF:
        raise LazPerfNotFound('Cannot manipulate laz data')


def is_point_format_compressed(point_format_id):
    compression_bit_7 = (point_format_id & 0x80) >> 7
    compression_bit_6 = (point_format_id & 0x40) >> 6
    if not compression_bit_6 and compression_bit_7:
        return True
    return False


def compressed_id_to_uncompressed(point_format_id):
    return point_format_id & 0x3f


def uncompressed_id_to_compressed(point_format_id):
    return (2 ** 7) | point_format_id


def decompress_buffer(compressed_buffer, point_format_id, point_count, laszip_vlr):
    raise_if_no_lazperf()

    ndtype = get_dtype_of_format_id(point_format_id)
    point_compressed = np.frombuffer(compressed_buffer, dtype=np.uint8)

    vlr_data = np.frombuffer(laszip_vlr.record_data, dtype=np.uint8)
    decompressor = lazperf.VLRDecompressor(point_compressed, vlr_data)

    point_uncompressed = decompressor.decompress_points(point_count)

    point_uncompressed = np.frombuffer(point_uncompressed, dtype=ndtype, count=point_count)

    return point_uncompressed


def create_laz_vlr(point_format_id):
    raise_if_no_lazperf()
    record_schema = lazperf.RecordSchema()

    if 'gps_time' in POINT_FORMAT_DIMENSIONS[point_format_id]:
        record_schema.add_gps_time()

    if 'red' in POINT_FORMAT_DIMENSIONS[point_format_id]:
        record_schema.add_rgb()

    return lazperf.LazVLR(record_schema)


def compress_buffer(uncompressed_buffer, record_schema, offset):
    raise_if_no_lazperf()

    compressor = lazperf.VLRCompressor(record_schema, offset)
    uncompressed_buffer = np.frombuffer(uncompressed_buffer, dtype=np.uint8)
    compressed = compressor.compress(uncompressed_buffer)

    return compressed


def _pass_through_laszip(stream, action='decompress'):
    laszip_names = ('laszip', 'laszip.exe', 'laszip-cli', 'laszip-cli.exe')

    for binary in laszip_names:
        in_path = [os.path.isfile(os.path.join(x, binary)) for x in os.environ["PATH"].split(os.pathsep)]
        if any(in_path):
            laszip_binary = binary
            break
    else:
        raise FileNotFoundError('No laszip')

    if action == "decompress":
        out_t = '-olas'
    elif action == "compress":
        out_t = '-olaz'
    else:
        raise ValueError('Invalid Action')

    prc = subprocess.Popen(
        [laszip_binary, "-stdin", out_t, "-stdout"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    data, stderr = prc.communicate(stream.read())
    if prc.returncode != 0:
        raise RuntimeError("Laszip failed to {} with error code {}\n\t{}".format(
            action, prc.returncode, '\n\t'.join(stderr.decode().splitlines())
        ))
    return data


def laszip_compress(stream):
    return _pass_through_laszip(stream, action='compress')


def laszip_decompress(stream):
    return _pass_through_laszip(stream, action='decompress')
