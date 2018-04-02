import mmap

from . import headers
from .point import record
from .vlrs import vlrlist


class LasMMAP:
    def __init__(self, filename):
        self.fileref = open(filename, mode='r+b')
        self.mmap = mmap.mmap(self.fileref.fileno(), length=0, access=mmap.ACCESS_WRITE)
        self.header = headers.HeaderFactory.from_mmap(self.mmap)
        if self.header.are_points_compressed:
            raise ValueError('Cannot mmap a compressed LAZ file')

        self.mmap.seek(self.header.header_size)
        self.vlrs = vlrlist.VLRList.read_from(self.mmap, self.header.number_of_vlr)

        try:
            extra_dims = self.vlrs.get('ExtraBytesVlr')[0].type_of_extra_dims()
        except IndexError:
            extra_dims = None

        self.points = record.PackedPointRecord.from_buffer(
            self.mmap,
            self.header.point_data_format_id,
            count=self.header.number_of_point_records,
            offset=self.header.offset_to_point_data,
            extra_dims=extra_dims
        )

    def close(self):
        self.header = None  # To delete pointer to mapped data
        self.mmap.close()
        self.fileref.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
