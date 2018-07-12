""" The functions related to the LAZ format (compressed LAS)
Lazperf is made optional by catching the ModuleNotFoundError, and raising an exception
when compression/decompression is actually needed

There are also functions to use Laszip (meant to be used as a fallback)
"""
import os
import subprocess

import numpy as np

from .errors import LazPerfNotFound, PylasError
from .point.dims import get_dtype_of_format_id

HAS_LAZPERF = False

try:
    import lazperf

    HAS_LAZPERF = True
    # we should capture ModuleNotRoundError but it's a python3.6 exception type
    # and ReadTheDocs uses 3.5
except:
    HAS_LAZPERF = False


def raise_if_no_lazperf():
    if not HAS_LAZPERF:
        raise LazPerfNotFound("Cannot manipulate laz data")
    elif lazperf.__version__ < '1.3.0':
        raise LazPerfNotFound("Version >= 1.3.0 required, you have {}".format(lazperf.__version__))


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


def decompress_buffer(compressed_buffer, points_dtype, point_count, laszip_vlr):
    raise_if_no_lazperf()

    point_compressed = np.frombuffer(compressed_buffer, dtype=np.uint8)

    vlr_data = np.frombuffer(laszip_vlr.record_data, dtype=np.uint8)
    decompressor = lazperf.VLRDecompressor(point_compressed, points_dtype.itemsize, vlr_data)

    point_uncompressed = decompressor.decompress_points(point_count)

    point_uncompressed = np.frombuffer(
        point_uncompressed, dtype=points_dtype, count=point_count
    )

    return point_uncompressed


def create_laz_vlr(points_record):
    raise_if_no_lazperf()
    record_schema = lazperf.RecordSchema()

    if points_record.point_format_id >= 6:
        raise PylasError("Can't compress points with format it >= 6")
    record_schema.add_point()

    if "gps_time" in points_record.dimensions_names:
        record_schema.add_gps_time()

    if "red" in points_record.dimensions_names:
        record_schema.add_rgb()

    official_dtype = get_dtype_of_format_id(points_record.point_format_id)

    num_extra_bytes = points_record.array.dtype.itemsize - official_dtype.itemsize
    if num_extra_bytes > 0:
        record_schema.add_extra_bytes(num_extra_bytes)
    elif num_extra_bytes < 0:
        raise PylasError("Incoherent number of extra bytes ({})".format(num_extra_bytes))

    return lazperf.LazVLR(record_schema)


def compress_buffer(uncompressed_buffer, record_schema, offset):
    raise_if_no_lazperf()

    compressor = lazperf.VLRCompressor(record_schema, offset)
    uncompressed_buffer = np.frombuffer(uncompressed_buffer, dtype=np.uint8)
    compressed = compressor.compress(uncompressed_buffer)

    return compressed


def find_laszip_executable():
    laszip_names = ("laszip", "laszip.exe", "laszip-cli", "laszip-cli.exe")

    for binary in laszip_names:
        in_path = (
            os.path.isfile(os.path.join(x, binary))
            for x in os.environ["PATH"].split(os.pathsep)
        )
        if any(in_path):
            return binary

    else:
        return None


def _pass_through_laszip(stream, action="decompress"):
    laszip_binary = find_laszip_executable()
    if laszip_binary is None:
        raise FileNotFoundError("Could not find laszip executable")

    if action == "decompress":
        out_t = "-olas"
    elif action == "compress":
        out_t = "-olaz"
    else:
        raise ValueError("Invalid Action")

    prc = subprocess.Popen(
        [laszip_binary, "-stdin", out_t, "-stdout"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    data, stderr = prc.communicate(stream.read())
    if prc.returncode != 0:
        raise RuntimeError(
            "Laszip failed to {} with error code {}\n\t{}".format(
                action, prc.returncode, "\n\t".join(stderr.decode().splitlines())
            )
        )
    return data


def laszip_compress(stream):
    return _pass_through_laszip(stream, action="compress")


def laszip_decompress(stream):
    return _pass_through_laszip(stream, action="decompress")
