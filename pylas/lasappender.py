import io
import math
from typing import Union, Iterable, BinaryIO

from .headers.rawheader import Header
from .vlrs.vlrlist import VLRList
from .compression import LazBackend
from .errors import PylasError
from .evlrs import EVLRList, RawEVLRList
from .lasreader import LasReader, get_extra_dims_info_tuple
from .laswriter import UncompressedPointWriter
from .point.format import PointFormat
from .point.record import PointRecord

try:
    import lazrs
except ModuleNotFoundError:
    pass


class LazrsAppender:
    """Appending in LAZ file works by seeking to start of the last chunk
    of compressed points, decompress it while keeping the points in
    memory.

    Then seek back to the start of the last chunk, and recompress
    the points we just read, so that we have a compressor in the proper state
    ready to compress new points.
    """

    def __init__(
        self, dest: BinaryIO, header: Header, vlrs: VLRList, parallel: bool
    ) -> None:
        self.dest = dest
        self.offset_to_point_data = header.offset_to_point_data
        laszip_vlr = vlrs.pop(vlrs.index("LasZipVlr"))

        self.dest.seek(header.offset_to_point_data, io.SEEK_SET)
        decompressor = lazrs.LasZipDecompressor(self.dest, laszip_vlr.record_data)
        vlr = decompressor.vlr()
        number_of_complete_chunk = int(
            math.floor(header.point_count / vlr.chunk_size())
        )

        self.dest.seek(header.offset_to_point_data, io.SEEK_SET)
        chunk_table = lazrs.read_chunk_table(self.dest)
        if chunk_table is None:
            # The file does not have a chunk table
            # we cannot seek to the last chunk, so instead, we will
            # decompress points (which is slower) and build the chunk table
            # to write it later

            self.chunk_table = []
            start_of_chunk = self.dest.tell()
            point_buf = bytearray(vlr.chunk_size() * vlr.item_size())

            for _ in range(number_of_complete_chunk):
                decompressor.decompress_many(point_buf)
                pos = self.dest.tell()
                self.chunk_table.append(pos - start_of_chunk)
                start_of_chunk = pos
        else:
            self.chunk_table = chunk_table[:-1]
            idx_first_point_of_last_chunk = number_of_complete_chunk * vlr.chunk_size()
            decompressor.seek(idx_first_point_of_last_chunk)

        points_of_last_chunk = bytearray(
            (header.point_count % vlr.chunk_size()) * vlr.item_size()
        )
        decompressor.decompress_many(points_of_last_chunk)

        self.dest.seek(header.offset_to_point_data, io.SEEK_SET)
        if parallel:
            self.compressor = lazrs.ParLasZipCompressor(
                self.dest, vlr
            )  # This overwrites old offset
        else:
            self.compressor = lazrs.LasZipCompressor(
                self.dest, vlr
            )  # This overwrites the old offset
        self.dest.seek(sum(self.chunk_table), io.SEEK_CUR)
        self.compressor.compress_many(points_of_last_chunk)

    def write_points(self, points: PointRecord) -> None:
        self.compressor.compress_many(points.memoryview())

    def done(self) -> None:
        # The chunk table written is at the good position
        # but it is incomplete (it's missing the chunk_table of
        # chunks before the one we appended)
        self.compressor.done()

        # So we update it
        self.dest.seek(self.offset_to_point_data, io.SEEK_SET)
        offset_to_chunk_table = int.from_bytes(self.dest.read(8), "little", signed=True)
        self.dest.seek(-8, io.SEEK_CUR)
        chunk_table = self.chunk_table + lazrs.read_chunk_table(self.dest)
        self.dest.seek(offset_to_chunk_table, io.SEEK_SET)
        lazrs.write_chunk_table(self.dest, chunk_table)


class LasAppender:
    def __init__(
        self,
        dest: BinaryIO,
        laz_backend: Union[LazBackend, Iterable[LazBackend]] = (
            LazBackend.LazrsParallel,
            LazBackend.Lazrs,
        ),
        closefd: bool = True,
    ) -> None:
        if not dest.seekable():
            raise TypeError("Expected the 'dest' to be a seekable file object")
        header, vlrs = LasReader._read_header_and_vlrs(dest, seekable=True)

        self.dest = dest
        self.header = header
        self.vlrs = vlrs
        self.point_format = PointFormat(
            self.header.point_format_id,
            get_extra_dims_info_tuple(self.header, self.vlrs),
        )

        if not header.are_points_compressed:
            self.points_writer = UncompressedPointWriter(self.dest)
            self.dest.seek(
                (self.header.point_count * self.header.point_size)
                + self.header.offset_to_point_data,
                io.SEEK_SET,
            )
        else:
            self.points_writer = self._create_laz_backend(laz_backend)

        if header.version >= "1.4" and header.number_of_evlr > 0:
            assert (
                self.dest.tell() <= self.header.start_of_first_evlr
            ), "The position is past the start of evlrs"
            pos = self.dest.tell()
            self.dest.seek(self.header.start_of_first_evlr, io.SEEK_SET)
            self.evlrs = EVLRList.read_from(self.dest, self.header.number_of_evlr)
            dest.seek(self.header.start_of_first_evlr, io.SEEK_SET)
            self.dest.seek(pos, io.SEEK_SET)
        elif header.version >= "1.4":
            self.evlrs = []

        self.closefd = closefd

    def append_points(self, points: PointRecord) -> None:
        if points.point_format != self.point_format:
            raise PylasError("Point formats do not match")

        self.points_writer.write_points(points)
        self.header.update(points)

    def close(self) -> None:
        self.points_writer.done()
        self._write_evlrs()
        self._write_updated_header()

        if self.closefd:
            self.dest.close()

    def _write_evlrs(self) -> None:
        if self.header.version >= "1.4" and len(self.evlrs) > 0:
            self.header.number_of_evlr = len(self.evlrs)
            self.header.start_of_first_evlr = self.dest.tell()
            raw_evlrs = RawEVLRList.from_list(self.evlrs)
            raw_evlrs.write_to(self.dest)

    def _write_updated_header(self) -> None:
        pos = self.dest.tell()
        self.dest.seek(0, io.SEEK_SET)
        self.header.write_to(self.dest)
        self.dest.seek(pos, io.SEEK_SET)

    def _create_laz_backend(
        self,
        laz_backend: Union[LazBackend, Iterable[LazBackend]] = (
            LazBackend.LazrsParallel,
            LazBackend.Lazrs,
        ),
    ) -> LazrsAppender:
        try:
            laz_backend = iter(laz_backend)
        except TypeError:
            laz_backend = (laz_backend,)

        last_error = None
        for backend in laz_backend:
            if backend == LazBackend.Laszip:
                raise PylasError("Laszip backend does not support appending")
            elif backend == LazBackend.LazrsParallel:
                try:
                    return LazrsAppender(
                        self.dest, self.header, self.vlrs, parallel=True
                    )
                except Exception as e:
                    last_error = e
            elif backend == LazBackend.Lazrs:
                try:
                    return LazrsAppender(
                        self.dest, self.header, self.vlrs, parallel=False
                    )
                except Exception as e:
                    last_error = e

        if last_error is not None:
            raise PylasError(f"Could not initialize a laz backend: {last_error}")
        else:
            raise PylasError(f"No valid laz backend selected")

    def __enter__(self) -> "LasAppender":
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.close()
