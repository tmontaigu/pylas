from .base import LasBase
from ..laswriter import LasWriter
from ..utils import ctypes_max_limit
from ..compression import LazBackend


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

        if len(self.points) > ctypes_max_limit(
            self.header.__class__.legacy_point_count.size
        ):
            self.header.legacy_point_count = 0
        else:
            self.header.legacy_point_count = len(self.points)

    def write_to(
        self, out_stream, do_compress=False, laz_backend=LazBackend.detect_available()
    ):
        with LasWriter(
            out_stream,
            self.header,
            self.vlrs,
            do_compress=do_compress,
            closefd=False,
            laz_backend=laz_backend,
        ) as writer:
            writer.write(self.points)
            writer.write_evlrs(self.evlrs)
