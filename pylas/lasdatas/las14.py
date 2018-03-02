from .base import LasBase


class LasData(LasBase):
    def __init__(self, *, header=None, vlrs=None, points=None, evlrs=None):
        super().__init__(header=header, vlrs=vlrs, points=points)
        self.evlrs = evlrs

    def write_to(self, out_stream, do_compress=False):
        if do_compress:
            raise NotImplementedError('LazPerf cannot compress 1.4 file for the moment')
        super().write_to(out_stream, do_compress=False)
