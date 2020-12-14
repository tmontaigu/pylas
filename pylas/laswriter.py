import abc
import io
import logging
from copy import copy
from typing import BinaryIO, Optional, Union, Iterable

import numpy as np

from .compression import LazBackend
from .errors import PylasError
from .evlrs import EVLRList, RawEVLRList
from .header import LasHeader
from .point import dims
from .point.format import PointFormat
from .point.record import PointRecord
from .vlrs.known import LasZipVlr

logger = logging.getLogger(__name__)

try:
    import lazrs
except ModuleNotFoundError:
    pass

try:
    import laszipy
except ModuleNotFoundError:
    pass


class PointWriter(abc.ABC):
    @property
    @abc.abstractmethod
    def destination(self):
        ...

    def write_initial_header_and_vlrs(self, header: LasHeader):
        header.write_to(self.destination)

    @abc.abstractmethod
    def write_points(self, points):
        ...

    @abc.abstractmethod
    def done(self):
        ...

    def write_updated_header(self, header):
        self.destination.seek(0, io.SEEK_SET)
        header.write_to(self.destination)


class LasWriter:
    def __init__(
        self,
        dest: BinaryIO,
        header: LasHeader,
        do_compress: bool = False,
        laz_backend: Union[
            LazBackend, Iterable[LazBackend]
        ] = LazBackend.detect_available(),
        closefd: bool = True,
    ) -> None:
        self.closefd = closefd
        self.header = copy(header)
        self.header.partial_reset()
        self.header.maxs = [np.finfo("f8").min] * 3
        self.header.mins = [np.finfo("f8").max] * 3

        self.do_compress = do_compress
        self.laz_backend = laz_backend
        self.dest = dest
        self.done = False

        # These will be initialized on the first call to `write`
        self.point_writer: PointWriter

        dims.raise_if_version_not_compatible_with_fmt(
            header.point_format.id, str(self.header.version)
        )
        self.header.are_points_compressed = self.do_compress

        if self.do_compress:
            self.point_writer = self._create_laz_backend(self.laz_backend)
        else:
            self.point_writer = UncompressedPointWriter(self.dest)

        self.point_writer.write_initial_header_and_vlrs(self.header)

    def write(self, points: PointRecord) -> None:
        if not points:
            return

        if self.done:
            raise PylasError("Cannot write points anymore")

        if points.point_format != self.header.point_format:
            raise PylasError("Incompatible point formats")

        self.header.update(points)
        self.point_writer.write_points(points)

    def write_evlrs(self, evlrs: EVLRList) -> None:
        if self.header.version.minor < 4:
            raise PylasError(
                "EVLRs are not supported on files with version less than 1.4"
            )

        if len(evlrs) > 0:
            self.point_writer.done()
            self.done = True
            self.header.number_of_evlrs = len(evlrs)
            self.header.start_of_first_evlr = self.dest.tell()
            raw_evlrs = RawEVLRList.from_list(evlrs)
            raw_evlrs.write_to(self.dest)

    def close(self) -> None:
        if self.point_writer is not None:
            if not self.done:
                self.point_writer.done()
            self.point_writer.write_updated_header(self.header)
        if self.closefd:
            self.dest.close()

    def _create_laz_backend(
        self, laz_backends: Union[LazBackend, Iterable[LazBackend]]
    ) -> PointWriter:
        try:
            laz_backends = iter(laz_backends)
        except TypeError:
            laz_backends = (laz_backends,)

        last_error: Optional[Exception] = None
        for backend in laz_backends:
            try:
                if not backend.is_available():
                    raise PylasError(f"The '{backend}' is not available")

                if backend == LazBackend.Laszip:
                    return LaszipPointWriter(self.dest, self.header)
                elif backend == LazBackend.LazrsParallel:
                    return LazrsPointWriter(
                        self.dest, self.header.point_format, parallel=True
                    )
                elif backend == LazBackend.Lazrs:
                    return LazrsPointWriter(
                        self.dest, self.header.point_format, parallel=False
                    )
                else:
                    raise PylasError("Unknown LazBacked: {}".format(backend))
            except Exception as e:
                logger.error(e)
                last_error = e

        if last_error is not None:
            raise PylasError("No LazBackend selected, cannot compress")
        else:
            raise PylasError(f"No LazBackend could be initialized: {last_error}")

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()


class UncompressedPointWriter(PointWriter):
    def __init__(self, dest):
        self.dest = dest

    @property
    def destination(self):
        return self.dest

    def write_points(self, points):
        self.dest.write(points.memoryview())

    def done(self):
        pass


class LaszipPointWriter(PointWriter):
    def __init__(self, dest: BinaryIO, header: LasHeader):
        self.dest = dest
        header.set_compressed(False)
        with io.BytesIO() as tmp:
            header.write_to(tmp)
            header_bytes = tmp.getvalue()

        self.zipper = laszipy.LasZipper(self.dest, header_bytes)
        zipper_header = self.zipper.header
        assert zipper_header.point_data_format == header.point_format.id
        assert zipper_header.point_data_record_length == header.point_format.size

        header.set_compressed(True)

    @property
    def destination(self):
        return self.dest

    def write_points(self, points):
        points_bytes = np.frombuffer(points.array, np.uint8)
        self.zipper.compress(points_bytes)

    def done(self):
        self.zipper.done()

    def write_initial_header_and_vlrs(self, header: LasHeader):
        # Do nothing as creating the laszip zipper writes the header and vlrs
        pass

    def write_updated_header(self, header):
        # Again, do nothing as the closing the laszip zipper will
        # update the header for us
        pass


class LazrsPointWriter(PointWriter):
    def __init__(self, dest: BinaryIO, point_format: PointFormat, parallel: bool):
        self.dest = dest
        self.vlr = lazrs.LazVlr.new_for_compression(
            point_format.id, point_format.num_extra_bytes
        )
        self.parallel = parallel
        self.compressor: Optional[
            Union[lazrs.ParLasZipCompressor, lazrs.LasZipCompressor]
        ] = None

    def write_initial_header_and_vlrs(self, header):
        laszip_vlr = LasZipVlr(self.vlr.record_data())
        header.vlrs.append(laszip_vlr)
        super().write_initial_header_and_vlrs(header)
        # We have to initialize our compressor here
        # because on init, it writes the offset to chunk table
        # so the header and vlrs have to be written
        if self.parallel:
            self.compressor = lazrs.ParLasZipCompressor(self.dest, self.vlr)
        else:
            self.compressor = lazrs.LasZipCompressor(self.dest, self.vlr)

    @property
    def destination(self):
        return self.dest

    def write_points(self, points):
        assert (
            self.compressor is not None
        ), "Trying to write points without having written header"
        points_bytes = np.frombuffer(points.array, np.uint8)
        self.compressor.compress_many(points_bytes)

    def done(self):
        if self.compressor is not None:
            self.compressor.done()
