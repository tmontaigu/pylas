from .base import LasBase
from .. import evlrs
from .. import extradims
from ..utils import ctypes_max_limit
from ..vlrs.known import ExtraBytesVlr, ExtraBytesStruct


class LasData(LasBase):
    def __init__(self, *, header=None, vlrs=None, points=None, evlrs=None):
        super().__init__(header=header, vlrs=vlrs, points=points)
        self.evlrs = [] if evlrs is None else evlrs

    def update_header(self):
        super().update_header()
        if len(self.vlrs.get("WktCoordinateSystemVlr")) == 1:
            self.header.global_encoding.wkt = 1

    def add_extra_dim(self, name, type, description=''):
        name = name.replace(" ", "_")
        type_id = extradims.get_id_for_extra_dim_type(type)
        extra_byte = ExtraBytesStruct(data_type=type_id, name=name.encode(), description=description.encode())

        try:
            extra_bytes_vlr = self.vlrs.get("ExtraBytesVlr")[0]
        except IndexError:
            extra_bytes_vlr = ExtraBytesVlr()
            self.vlrs.append(extra_bytes_vlr)
        finally:
            extra_bytes_vlr.extra_bytes_structs.append(extra_byte)
            self.points_data.add_extra_dims([(name, type)])

    def write_to(self, out_stream, do_compress=False):
        if do_compress and self.points_data.point_format_id >= 6:
            raise NotImplementedError(
                "LazPerf cannot compress 1.4 files with point format >= 6"
            )

        start = out_stream.tell()
        self.header.start_of_waveform_data_packet_record = 0

        if len(self.points_data) > ctypes_max_limit(
            self.header.__class__.legacy_point_count.size
        ):
            self.header.legacy_point_count = 0
        else:
            self.header.legacy_point_count = len(self.points_data)
        super().write_to(out_stream, do_compress=do_compress)

        raw_evlrs = evlrs.RawEVLRList.from_list(self.evlrs)
        if len(self.evlrs) > 0:
            self.header.start_of_first_evlr = out_stream.tell()
            self.header.number_of_evlr = len(raw_evlrs)
        raw_evlrs.write_to(out_stream)
        out_stream.seek(start)
        self.header.write_to(out_stream)
