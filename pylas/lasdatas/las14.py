from .base import LasBase
from ..headers import rawheader


class LasData(LasBase):
    def __init__(self, *, header=None, vlrs=None, points=None, evlrs=None):
        super().__init__(header=header, vlrs=vlrs, points=points)
        self.evlrs = [] if evlrs is None else evlrs

    def write_to(self, out_stream, do_compress=False):
        if do_compress:
            raise NotImplementedError('LazPerf cannot compress 1.4 file for the moment')

        self.header.start_of_waveform_data_packet_record = 0
        self.header.start_of_first_evlr = 0
        self.header.number_of_evlr = len(self.evlrs)
        super().write_to(out_stream, do_compress=False)
        for evlr in self.evlrs:
            evlr.write_to(out_stream)
