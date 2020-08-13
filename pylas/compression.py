""" The functions related to the LAZ format (compressed LAS)
Lazperf is made optional by catching the ModuleNotFoundError, and raising an exception
when compression/decompression is actually needed

There are also functions to use Laszip (meant to be used as a fallback)
"""
import enum
import os
import subprocess
from enum import Enum, auto
from typing import List

import numpy as np

from .errors import PylasError, LazError

HAS_LAZPERF = False

try:
    import lazperf

    HAS_LAZPERF = True
    # we should capture ModuleNotFoundError but it's a python3.6 exception type
    # and ReadTheDocs uses 3.5
except:
    HAS_LAZPERF = False


def raise_if_no_lazperf():
    if not HAS_LAZPERF:
        raise LazError("Lazperf is not installed")
    elif lazperf.__version__ < "1.3.0":
        raise LazError(
            "Version >= 1.3.0 required, you have {}".format(lazperf.__version__)
        )


class LazBackend(enum.Enum):
    LazrsParallel = 0
    Lazrs = 1
    Laszip = 2

    def is_available(self) -> bool:
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
    def detect_available() -> List['LazBackend']:
        available_backends = []

        if LazBackend.LazrsParallel.is_available():
            available_backends.append(LazBackend.LazrsParallel)
            available_backends.append(LazBackend.Lazrs)

        if LazBackend.Laszip.is_available():
            available_backends.append(LazBackend.Laszip)

        return available_backends

    @staticmethod
    def all() -> List['LazBackend']:
        return LazBackend.LazrsParallel, LazBackend.Lazrs, LazBackend.Laszip


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


def lazrs_decompress_buffer(compressed_buffer, point_size, point_count, laszip_vlr, parallel=True):
    try:
        import lazrs
    except Exception as e:
        raise LazError("lazrs is not installed") from e

    try:
        point_compressed = np.frombuffer(compressed_buffer, dtype=np.uint8)
        vlr_data = np.frombuffer(laszip_vlr.record_data, dtype=np.uint8)

        point_decompressed = np.zeros(point_count * point_size, np.uint8)

        lazrs.decompress_points(point_compressed, vlr_data, point_decompressed, parallel)
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
            points_data.point_format.id, points_data.point_format.num_extra_bytes)

        compressed_data = lazrs.compress_points(
            vlr,
            np.frombuffer(points_data.array, np.uint8),
            parallel
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
        decompressor = lazperf.VLRDecompressor(
            point_compressed, point_size, vlr_data
        )

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


class LasZipProcess:
    class Actions(Enum):
        Compress = auto()
        Decompress = auto()

    def __init__(self, action, stdin=subprocess.PIPE, stdout=subprocess.PIPE):
        """ Creates a Popen to the laszip executable.

        This tries to be a wrapper for
        https://docs.python.org/fr/3/library/subprocess.html#subprocess.Popen

        Valid inputs for `stdin` and `stdout` are file objects supporting
        the fileno() method. For example files opened with  `open`.

        The usage is kinda tricky:
        """
        laszip_binary = find_laszip_executable()

        if action == LasZipProcess.Actions.Decompress:
            out_t = "-olas"
        elif action == LasZipProcess.Actions.Compress:
            out_t = "-olaz"
        else:
            raise ValueError("Invalid Action")

        self.prc = subprocess.Popen(
            [laszip_binary, "-stdin", out_t, "-stdout"],
            stdin=stdin,
            stdout=stdout,
            stderr=subprocess.PIPE,
        )

    @property
    def stdin(self):
        return self.prc.stdin

    @property
    def stdout(self):
        return self.prc.stdout

    def wait(self):
        return self.prc.wait()

    def communicate(self):
        stdout_data, stderr_data = self.prc.communicate()
        self.raise_if_bad_err_code(stderr_data.decode())
        return stdout_data

    def raise_if_bad_err_code(self, error_msg=None):
        if error_msg is None:
            error_msg = self.prc.stderr.read().decode()
        if self.prc.returncode != 0:
            raise RuntimeError(
                "Laszip failed to {} with error code {}\n\t{}".format(
                    "compress", self.prc.returncode, "\n\t".join(error_msg.splitlines())
                )
            )

    def wait_until_finished(self):
        self.stdin.close()
        self.prc.wait()
        self.raise_if_bad_err_code(self.prc.stderr.read().decode())
