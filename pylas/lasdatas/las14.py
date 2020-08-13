from .base import LasBase
from .. import evlrs
from ..headers.rawheader import RawHeader1_4
from ..utils import ctypes_max_limit
from ..vlrs import vlrlist
from ..laswriter import LasWriter


class LasData(LasBase):
    def __init__(self, *, header=None, vlrs=None, points=None, evlrs=None):
        super().__init__(header=header, vlrs=vlrs, points=points)
        self.laszip_was_called = False
        self.evlrs = [] if evlrs is None else evlrs

    def update_header(self):
        super().update_header()
        if len(self.vlrs.get("WktCoordinateSystemVlr")) == 1:
            self.header.global_encoding.wkt = 1

        self.header.start_of_waveform_data_packet_record = 0

        if len(self.points_data) > ctypes_max_limit(
                self.header.__class__.legacy_point_count.size
        ):
            self.header.legacy_point_count = 0
        else:
            self.header.legacy_point_count = len(self.points_data)

    def write_to(self, out_stream, do_compress=False):
        with LasWriter(out_stream, self.header, self.vlrs, do_compress=do_compress, closefd=False) as writer:
            writer.write(self.points_data)
            writer.write_evlrs(self.evlrs)

    #     # When compressing data, we cannot know in advance the size of the compressed points
    #     # LAS 1.4 may have evlrs located after the point data, and the header has a field
    #     # that must give the offset to first evlr
    #     # so in the case of writing compressed points we have to update the header
    #     # written afterwards with seek + write
    #     start = out_stream.tell()
    #     if not do_compress:
    #         if len(self.evlrs) > 0:
    #             self.header.number_of_evlr = len(self.evlrs)
    #             raw_vlrs = vlrlist.RawVLRList.from_list(self.vlrs)
    #             self.header.start_of_first_evlr = (self.header.point_size * self.header.point_count) + self.header.size + raw_vlrs.total_size_in_bytes()
    #
    #         super().write_to(out_stream, do_compress=do_compress)
    #         if len(self.evlrs) > 0:
    #             raw_evlrs = evlrs.RawEVLRList.from_list(self.evlrs)
    #             raw_evlrs.write_to(out_stream)
    #     else:
    #         super().write_to(out_stream, do_compress=do_compress)
    #         # if laszip was called, the out_stream already contains the evlrs
    #         # because we were called with write_to(laszip_sdtin, do_compress=False)
    #         # and laszip has taken care of writting the LAZ file, so we do not have to
    #         # write evlrs
    #         if len(self.evlrs) > 0 and not self.laszip_was_called:
    #             self.header.number_of_evlr = len(self.evlrs)
    #             self.header.start_of_first_evlr = out_stream.tell()
    #             self.header.update_evlrs_info_in_stream(self, out_stream, start)
    #             out_stream.seek(self.header.start_of_first_evlr)
    #             raw_evlrs = evlrs.RawEVLRList.from_list(self.evlrs)
    #             raw_evlrs.write_to(out_stream)
    #             self.laszip_was_called = False

    def _compress_with_laszip_executable(self, out_stream):
        super()._compress_with_laszip_executable(out_stream)
        self.laszip_was_called = True
