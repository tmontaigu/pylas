from .base import LasBase
from .. import extradims
from ..vlrs.known import ExtraBytesVlr, ExtraBytesStruct
from .. import evlr


def ctypes_max_limit(byte_size, signed=False):
    nb_bits = (byte_size * 8) - (1 if signed else 0)
    return (2 ** nb_bits) - 1


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
        if len(self.points_data) > ctypes_max_limit(self.header.__class__.legacy_number_of_point_records.size):
            self.header.legacy_number_of_point_records = 0
        else:
            self.header.legacy_number_of_point_records = len(self.points_data)
        super().write_to(out_stream, do_compress=do_compress)
        raw_evlrs = evlr.RawEVLRList.from_list(self.evlrs)
        raw_evlrs.write_to(out_stream)
