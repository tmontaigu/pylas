import mmap

from . import headers
from .lasdatas import base
from .point import record
from .vlrs import vlrlist

from . import lasreader


class LasMMAP(base.LasBase):
    """ Memory map a LAS file.
    It works like a regular LasData however the data is not actually read in memory
    which is useful for large files.

    .. note::
        A LAZ (compressed LAS) cannot be mmapped

    Changes made to the header or points data is directly done in the file.

    VLRs are an exception, they are read and held into memory, (it is not a problem
    as its the point data that actually account for most of a LAS file payload).
    VLRS are written when closing the file so any changes to them is not directly reflected
    """

    def __init__(self, filename):
        fileref = open(filename, mode='r+b')
        lasreader._raise_if_wrong_file_signature(fileref)

        m = mmap.mmap(fileref.fileno(), length=0, access=mmap.ACCESS_WRITE)
        header = headers.HeaderFactory.from_mmap(m)
        if header.are_points_compressed:
            raise ValueError('Cannot mmap a compressed LAZ file')
        super().__init__(header=header)
        self.fileref, self.mmap = fileref, m
        self.mmap.seek(self.header.size)
        self.vlrs = vlrlist.VLRList.read_from(self.mmap, self.header.number_of_vlr)

        try:
            extra_dims = self.vlrs.get('ExtraBytesVlr')[0].type_of_extra_dims()
        except IndexError:
            extra_dims = None

        self.points_data = record.PackedPointRecord.from_buffer(
            self.mmap,
            self.header.point_data_format_id,
            count=self.header.point_count,
            offset=self.header.offset_to_point_data,
            extra_dims=extra_dims
        )

    def _write_vlrs(self):
        raw_vlrs = vlrlist.RawVLRList(vlr.into_raw() for vlr in self.vlrs)

        original_vlrs_bytes_len = self.header.offset_to_point_data - self.header.size
        bytes_len_diff = original_vlrs_bytes_len - raw_vlrs.total_size_in_bytes()
        old_offset = self.header.offset_to_point_data
        new_offset = old_offset - bytes_len_diff
        points_bytes_len = self.points_data.actual_point_size * len(self.points_data)
        header_size = self.header.size

        self.header.offset_to_point_data = new_offset
        self.header.number_of_vlr = len(raw_vlrs)
        # To be able to use mmap.resize(),
        # the header must be set to None so that the ctypes structure
        # releases its pointer the the mmap buffer
        self.header = None
        self.points_data = record.PackedPointRecord.empty(0)

        if bytes_len_diff > 0:
            self.mmap.move(new_offset, old_offset, points_bytes_len)
            self.mmap.resize(len(self.mmap) - bytes_len_diff)
        elif bytes_len_diff < 0:
            self.mmap.resize(len(self.mmap) - bytes_len_diff)
            self.mmap.move(new_offset, old_offset, points_bytes_len)

        self.mmap.seek(header_size)
        raw_vlrs.write_to(self.mmap)

    def close(self):
        self._write_vlrs()
        self.mmap.close()
        self.fileref.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
