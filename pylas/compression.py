""" The functions related to the LAZ format (compressed LAS)
Lazperf is made optional by catching the ModuleNotFoundError, and raising an exception
when compression/decompression is actually needed

There are also functions to use Laszip (meant to be used as a fallback)
"""
import enum
import os
from typing import Tuple

import numpy as np

from .errors import PylasError, LazError

HAS_LAZPERF = False

try:
    import lazperf
except ModuleNotFoundError:
    HAS_LAZPERF = False
else:
    HAS_LAZPERF = True


def raise_if_no_lazperf():
    if not HAS_LAZPERF:
        raise LazError("Lazperf is not installed")
    elif lazperf.__version__ < "1.3.0":
        raise LazError(
            "Version >= 1.3.0 required, you have {}".format(lazperf.__version__)
        )


class LazBackend(enum.Enum):
    """Supported backends for reading and writing LAS/LAZ"""

    # type_hint = Union[LazBackend, Iterable[LazBackend]]

    LazrsParallel = 0
    Lazrs = 1
    Laszip = 2  # laszip executable, used through a Popen

    def is_available(self) -> bool:
        """Returns true if the backend is available"""
        if self == LazBackend.Lazrs or self == LazBackend.LazrsParallel:
            try:
                import lazrs
            except ModuleNotFoundError:
                return False
            else:
                return True
        elif self == LazBackend.Laszip:
            try:
                find_laszip_executable()
            except FileNotFoundError:
                return False
            else:
                return True
        else:
            return False

    @staticmethod
    def detect_available() -> Tuple["LazBackend"]:
        """Returns a tuple containing the available backends in the current
        python environment
        """
        available_backends = []

        if LazBackend.LazrsParallel.is_available():
            available_backends.append(LazBackend.LazrsParallel)
            available_backends.append(LazBackend.Lazrs)

        if LazBackend.Laszip.is_available():
            available_backends.append(LazBackend.Laszip)

        return tuple(available_backends)


def is_point_format_compressed(point_format_id):
    compression_bit_7 = (point_format_id & 0x80) >> 7
    compression_bit_6 = (point_format_id & 0x40) >> 6
    if not compression_bit_6 and compression_bit_7:
        return True
    return False


def compressed_id_to_uncompressed(point_format_id):
    return point_format_id & 0x3F


def uncompressed_id_to_compressed(point_format_id):
    return (2 ** 7) | point_format_id


def lazrs_decompress_buffer(
    compressed_buffer, point_size, point_count, laszip_vlr, parallel=True
):
    try:
        import lazrs
    except Exception as e:
        raise LazError("lazrs is not installed") from e

    try:
        point_compressed = np.frombuffer(compressed_buffer, dtype=np.uint8)
        vlr_data = np.frombuffer(laszip_vlr.record_data, dtype=np.uint8)

        point_decompressed = np.zeros(point_count * point_size, np.uint8)

        lazrs.decompress_points(
            point_compressed, vlr_data, point_decompressed, parallel
        )
    except lazrs.LazrsError as e:
        raise LazError("lazrs error: {}".format(e)) from e
    else:
        return point_decompressed


def lazrs_compress_points(points_data, parallel=True):
    try:
        import lazrs
    except Exception as e:
        raise LazError("lazrs is not installed") from e

    try:
        vlr = lazrs.LazVlr.new_for_compression(
            points_data.point_format.id, points_data.point_format.num_extra_bytes
        )

        compressed_data = lazrs.compress_points(
            vlr, np.frombuffer(points_data.array, np.uint8), parallel
        )
    except lazrs.LazrsError as e:
        raise LazError("lazrs error: {}".format(e)) from e
    else:
        return compressed_data, vlr.record_data()


def lazperf_decompress_buffer(compressed_buffer, point_size, point_count, laszip_vlr):
    raise_if_no_lazperf()

    try:
        point_compressed = np.frombuffer(compressed_buffer, dtype=np.uint8)

        vlr_data = np.frombuffer(laszip_vlr.record_data, dtype=np.uint8)
        decompressor = lazperf.VLRDecompressor(point_compressed, point_size, vlr_data)

        point_uncompressed = decompressor.decompress_points(point_count)

        return point_uncompressed
    except RuntimeError as e:
        raise LazError("lazperf error: {}".format(e))


def lazperf_create_laz_vlr(points_record):
    raise_if_no_lazperf()
    try:
        record_schema = lazperf.RecordSchema()

        if points_record.point_format.id >= 6:
            raise PylasError("Can't compress points with format id >= 6")
        record_schema.add_point()

        if "gps_time" in points_record.dimensions_names:
            record_schema.add_gps_time()

        if "red" in points_record.dimensions_names:
            record_schema.add_rgb()

        num_extra_bytes = points_record.point_format.num_extra_bytes
        if num_extra_bytes > 0:
            record_schema.add_extra_bytes(num_extra_bytes)
        elif num_extra_bytes < 0:
            raise PylasError(
                "Incoherent number of extra bytes ({})".format(num_extra_bytes)
            )

        return lazperf.LazVLR(record_schema)
    except RuntimeError as e:
        raise LazError("lazperf error: {}".format(e))


def lazperf_compress_points(points_data):
    try:
        laz_vrl = lazperf_create_laz_vlr(points_data)

        compressor = lazperf.VLRCompressor(laz_vrl.schema, 0)
        uncompressed_buffer = np.frombuffer(points_data.array, np.uint8)
        uncompressed_buffer = np.frombuffer(uncompressed_buffer, dtype=np.uint8)
        compressed = compressor.compress(uncompressed_buffer)

        return compressed, laz_vrl.data()
    except RuntimeError as e:
        raise LazError("lazperf error: {}".format(e))


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
        raise FileNotFoundError("Could not find laszip executable")
