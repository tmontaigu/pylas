from .base import LasBase
from .. import evlrs
from ..headers.rawheader import RawHeader1_4
from ..utils import ctypes_max_limit


class LasData(LasBase):
    def __init__(self, *, header=None, vlrs=None, points=None, evlrs=None):
        super().__init__(header=header, vlrs=vlrs, points=points)
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
        start = out_stream.tell()
        super().write_to(out_stream, do_compress=do_compress)

        raw_evlrs = evlrs.RawEVLRList.from_list(self.evlrs)
        if len(self.evlrs) > 0:
            self.header.start_of_first_evlr = out_stream.tell()
            self.header.number_of_evlr = len(raw_evlrs)
            self.header.update_evlrs_info_in_stream(self, out_stream, start)
            out_stream.seek(self.header.start_of_first_evlr)

        raw_evlrs.write_to(out_stream)
        out_stream.seek(start)
