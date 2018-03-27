from .base import LasBase
from .. import extradims
from ..vlrs.known import ExtraBytesVlr, ExtraBytesStruct


class LasData(LasBase):
    def __init__(self, *, header=None, vlrs=None, points=None, evlrs=None):
        super().__init__(header=header, vlrs=vlrs, points=points)
        self.evlrs = [] if evlrs is None else evlrs

    def add_extra_dim(self, dim_name, dim_type):
        name = dim_name.replace(' ', '_')
        type_id = extradims.get_id_for_extra_dim_type(dim_type)
        extra_byte = ExtraBytesStruct(data_type=type_id, name=name.encode())

        try:
            extra_bytes_vlr = self.vlrs.get('ExtraBytesVlr')[0]
        except IndexError:
            extra_bytes_vlr = ExtraBytesVlr()
            self.vlrs.append(extra_bytes_vlr)
        finally:
            extra_bytes_vlr.extra_bytes_structs.append(extra_byte)
            self.points_data.add_extra_dims([(name, dim_type)])

    def write_to(self, out_stream, do_compress=False):
        if do_compress and self.points_data.point_format_id >= 6:
            raise NotImplementedError('LazPerf cannot compress 1.4 files with point format >= 6')

        self.header.start_of_waveform_data_packet_record = 0
        self.header.start_of_first_evlr = 0
        self.header.number_of_evlr = len(self.evlrs)
        super().write_to(out_stream, do_compress=False)
        for evlr in self.evlrs:
            evlr.write_to(out_stream)
