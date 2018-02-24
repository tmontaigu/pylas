from .base import LasBase
from .. import pointdims


# TODO Classification_flags setter, and proper subfields
class LasData(LasBase):
    def __init__(self, header=None, vlrs=None, points=None):
        super().__init__(header, vlrs, points)

    @property
    def return_number(self):
        return pointdims.unpack(self.points_data['bit_fields'], pointdims.RETURN_NUMBER_MASK_1_4)

    @property
    def number_of_returns(self):
        return pointdims.unpack(self.points_data['bit_fields'], pointdims.NUMBER_OF_RETURNS_MASK_1_4)

    @property
    def classification_flags(self):
        return pointdims.unpack(self.points_data['classification_flags'], pointdims.CLASSIFICATION_FLAGS_MASK)

    @property
    def scanner_channel(self):
        return pointdims.unpack(self.points_data['classification_flags'], pointdims.SCANNER_CHANNEL_MASK)

    @property
    def scan_direction_flag(self):
        return pointdims.unpack(self.points_data['classification_flags'], pointdims.SCAN_DIRECTION_FLAG_MASK_1_4)

    @property
    def edge_of_flight_line(self):
        return pointdims.unpack(self.points_data['classification_flags'], pointdims.EDGE_OF_FLIGHT_LINE_MASK_1_4)

    # Setters #

    @return_number.setter
    def return_number(self, value):
        pointdims.pack_into(self.points_data['bit_fields'], value, pointdims.RETURN_NUMBER_MASK_1_4, inplace=True)

    @number_of_returns.setter
    def number_of_returns(self, value):
        pointdims.pack_into(self.points_data['bit_fields'], value, pointdims.NUMBER_OF_RETURNS_MASK_1_4, inplace=True)

    @scan_direction_flag.setter
    def scan_direction_flag(self, value):
        pointdims.pack_into(self.points_data['bit_fields'], value, pointdims.SCAN_DIRECTION_FLAG_MASK_1_4,
                            inplace=True)

    @edge_of_flight_line.setter
    def edge_of_flight_line(self, value):
        pointdims.pack_into(self.points_data['bifields'], value, pointdims.EDGE_OF_FLIGHT_LINE_MASK_1_4, inplace=True)

    def write_to(self, out_stream, do_compress=False):
        if do_compress:
            raise NotImplementedError('LazPerf cannot compress 1.4 file for the moment')
        super().write_to(out_stream, do_compress=False)
