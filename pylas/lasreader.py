import abc
import logging
import os
import subprocess
from typing import Optional, BinaryIO, Iterable, Union

from . import errors, evlrs
from .compression import LazBackend
from .compression import find_laszip_executable
from .header import LasHeader
from .lasdata import LasData
from .point import record
from .utils import ConveyorThread
from .vlrs.known import LasZipVlr

try:
    import lazrs
except ModuleNotFoundError:
    pass

logger = logging.getLogger(__name__)


class LasReader:
    """The reader class handles LAS and LAZ via one of the supported backend"""

    def __init__(
        self,
        source: BinaryIO,
        closefd: bool = True,
        laz_backend: Union[
            LazBackend, Iterable[LazBackend]
        ] = LazBackend.detect_available(),
    ):
        self.closefd = closefd
        self.laz_backend = laz_backend
        self.header = LasHeader.read_from(source)

        if self.header.are_points_compressed:
            if not laz_backend:
                raise errors.PylasError(
                    "No LazBackend selected, cannot decompress data"
                )
            self.point_source = self._create_laz_backend(source)
            if self.point_source is None:
                raise errors.PylasError(
                    "Data is compressed, but no LazBacked could be initialized"
                )
        else:
            self.point_source = UncompressedPointReader(
                source, self.header.point_format.size
            )

        self.points_read = 0

    def read_n_points(self, n: int) -> Optional[record.ScaleAwarePointRecord]:
        points_left = self.header.point_count - self.points_read
        if points_left <= 0:
            return None

        if n < 0:
            n = points_left
        else:
            n = min(n, points_left)

        r = record.PackedPointRecord.from_buffer(
            self.point_source.read_n_points(n), self.header.point_format, n
        )
        points = record.ScaleAwarePointRecord(
            r.array, r.point_format, self.header.scales, self.header.offsets
        )
        self.points_read += n
        return points

    def read(self) -> LasData:
        """Reads all the points not read and returns a LasData object"""
        points = self.read_n_points(-1)
        if points is None:
            points = record.PackedPointRecord.empty(self.header.point_format)

        las_data = LasData(header=self.header, points=points)
        if self.header.version.minor >= 4:
            if (
                self.header.are_points_compressed
                and not self.point_source.source.seekable()
            ):
                # We explicitly require seekable stream because we have to seek
                # past the chunk table of LAZ file
                raise errors.PylasError(
                    "source must be seekable, to read evlrs form LAZ file"
                )
            las_data.evlrs = self._read_evlrs(self.point_source.source, seekable=True)

        return las_data

    def chunk_iterator(self, points_per_iteration: int) -> "PointChunkIterator":
        """Returns an iterator, that will read points by chunks
        of the requested size

        :param points_per_iteration: number of points to be read with each iteration
        :return:
        """
        return PointChunkIterator(self, points_per_iteration)

    def close(self) -> None:
        """closes the file object used by the reader"""
        if self.closefd:
            self.point_source.close()

    def _create_laz_backend(self, source) -> Optional["IPointReader"]:
        try:
            backends = iter(self.laz_backend)
        except TypeError:
            backends = (self.laz_backend,)

        laszip_vlr = self.header.vlrs.pop(self.header.vlrs.index("LasZipVlr"))
        for backend in backends:
            try:
                if not backend.is_available():
                    raise errors.PylasError(f"The '{backend}' is not available")

                if backend == LazBackend.LazrsParallel:
                    return LazrsPointReader(source, laszip_vlr, parallel=True)
                elif backend == LazBackend.Lazrs:
                    return LazrsPointReader(source, laszip_vlr, parallel=False)
                elif backend == LazBackend.Laszip:
                    point_source = LasZipProcessPointReader(source, self.header)
                    LasHeader.read_from(point_source.process.stdout, seekable=False)
                    return point_source
                else:
                    raise errors.PylasError("Unknown LazBackend: {}".format(backend))

            except errors.LazError as e:
                logger.error(e)

    def _read_evlrs(self, source, seekable=False) -> Optional[evlrs.EVLRList]:
        """Reads the EVLRs of the file, will fail if the file version
        does not support evlrs
        """
        if (
            self.header.version.minor >= 4
            and self.points_read == self.header.point_count
        ):
            if seekable:
                source.seek(self.header.start_of_first_evlr)
            return evlrs.EVLRList.read_from(source, self.header.number_of_evlrs)
        else:
            return None

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()


class PointChunkIterator:
    def __init__(self, reader, points_per_iteration) -> None:
        self.reader = reader
        self.points_per_iteration = points_per_iteration

    def __next__(self) -> record.ScaleAwarePointRecord:
        points = self.reader.read_n_points(self.points_per_iteration)
        if points is None:
            raise StopIteration
        return points

    def __iter__(self):
        return self


class IPointReader(abc.ABC):
    """The interface to be implemented by the class that actually reads
    points from as LAS/LAZ file so that the LasReader can use it.

    It is used to manipulate LAS/LAZ (with different LAZ backends) in the
    reader
    """

    @abc.abstractmethod
    def read_n_points(self, n) -> bytearray:
        ...

    @abc.abstractmethod
    def close(self):
        ...


class UncompressedPointReader(IPointReader):
    """Implementation of IPointReader for the simple uncompressed case"""

    def __init__(self, source, point_size) -> None:
        self.source = source
        self.point_size = point_size

    def read_n_points(self, n) -> bytearray:
        try:
            data = bytearray(n * self.point_size)
            self.source.readinto(data)
            return data
        except AttributeError:
            return bytearray(self.source.read(n * self.point_size))

    def close(self):
        self.source.close()


class LasZipProcessPointReader(IPointReader):
    """Implementation when using laszip executable as the LAZ backend.

    The compressed LAZ data (the whole file actually) is piped to laszip
    via its stdin and we get the uncompressed LAS data via its stdout


    when the source is a file object and not a file,
    we have to use a thread to move data from the file object to
    the laszip stdin to avoid a deadlock.
    """

    conveyor: Optional[ConveyorThread]

    def __init__(self, source, header: LasHeader) -> None:
        laszip_binary = find_laszip_executable()
        self.point_size: int = header.point_format.size
        if header.version.minor >= 4 and header.number_of_evlrs > 0:
            raise errors.PylasError(
                "Reading a LAZ file that contains EVLR using laszip is not supported"
            )
        try:
            fileno = source.fileno()
        except OSError:
            source.seek(0)
            self.source = source
            self.process = self.process = subprocess.Popen(
                [laszip_binary, "-stdin", "-olas", "-stdout"],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            self.conveyor = ConveyorThread(
                self.source, self.process.stdin, close_output=True
            )
            self.conveyor.start()
        else:
            os.lseek(fileno, 0, os.SEEK_SET)
            self.conveyor = None
            self.source = source
            self.process = self.process = subprocess.Popen(
                [laszip_binary, "-stdin", "-olas", "-stdout"],
                stdin=source,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )

    def read_n_points(self, n) -> bytearray:
        b = bytearray(n * self.point_size)
        self.process.stdout.readinto(b)
        if self.process.poll() is not None:
            self.raise_if_bad_err_code()
        return bytearray(b)

    def close(self):
        if self.conveyor is not None and self.conveyor.is_alive():
            self.conveyor.ask_for_termination()
            self.conveyor.join()

        if self.process.poll() is None:
            # We are likely getting closed before decompressing all the data
            self.process.terminate()
            self.process.wait()
        else:
            self.raise_if_bad_err_code()

        self.process.stdout.close()
        self.process.stderr.close()
        self.source.close()

    def raise_if_bad_err_code(self):
        if self.process is not None and self.process.returncode != 0:
            error_msg = self.process.stderr.read().decode()
            raise RuntimeError(
                "Laszip failed to {} with error code {}:\n\t{}".format(
                    "compress",
                    self.process.returncode,
                    "\n\t".join(error_msg.splitlines()),
                )
            )


class LazrsPointReader(IPointReader):
    """Implementation for the laz-rs backend, supports single-threaded decompression
    as well as multi-threaded decompression
    """

    def __init__(self, source, laszip_vlr: LasZipVlr, parallel: bool) -> None:
        self.source = source
        self.vlr = lazrs.LazVlr(laszip_vlr.record_data)
        if parallel:
            self.decompressor = lazrs.ParLasZipDecompressor(
                source, laszip_vlr.record_data
            )
        else:
            self.decompressor = lazrs.LasZipDecompressor(source, laszip_vlr.record_data)

    def read_n_points(self, n) -> bytearray:
        point_bytes = bytearray(n * self.vlr.item_size())
        self.decompressor.decompress_many(point_bytes)
        return point_bytes

    def close(self):
        self.source.close()
