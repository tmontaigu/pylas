import numpy as np

from .base import LasBase
from .. import vlr, pointdims


class LasData(LasBase):
    def __init__(self, header=None, vlrs=None, points=None):
        super().__init__(header, vlrs, points)

    @property
    def return_number(self):
        return pointdims.unpack(self.points_data['bit_fields'], pointdims.RETURN_NUMBER_MASK)

    @property
    def number_of_returns(self):
        return pointdims.unpack(self.points_data['bit_fields'], pointdims.NUMBER_OF_RETURNS_MASK)

    @property
    def scan_direction_flag(self):
        return pointdims.unpack(self.points_data['bit_fields'], pointdims.SCAN_DIRECTION_FLAG_MASK)

    @property
    def edge_of_flight_line(self):
        return pointdims.unpack(self.points_data['bit_fields'], pointdims.EDGE_OF_FLIGHT_LINE_MASK)

    @property
    def synthetic(self):
        return pointdims.unpack(self.points_data['raw_classification'], pointdims.SYNTHETIC_MASK).astype('bool')

    @property
    def key_point(self):
        return pointdims.unpack(self.points_data['raw_classification'], pointdims.KEY_POINT_MASK).astype('bool')

    @property
    def withheld(self):
        return pointdims.unpack(self.points_data['raw_classification'], pointdims.WITHHELD_MASK).astype('bool')

    @property
    def classification(self):
        return pointdims.unpack(self.points_data['raw_classification'], pointdims.CLASSIFICATION_MASK)

    # Setters #

    @number_of_returns.setter
    def number_of_returns(self, value):
        pointdims.pack_into(
            self.points_data['bit_fields'], value, pointdims.NUMBER_OF_RETURNS_MASK, inplace=True)

    @scan_direction_flag.setter
    def scan_direction_flag(self, value):
        pointdims.pack_into(
            self.points_data['bit_fields'], value, pointdims.SCAN_DIRECTION_FLAG_MASK, inplace=True)

    @edge_of_flight_line.setter
    def edge_of_flight_line(self, value):
        pointdims.pack_into(
            self.points_data['bit_fields'], value, pointdims.EDGE_OF_FLIGHT_LINE_MASK, inplace=True)

    @classification.setter
    def classification(self, value):
        pointdims.pack_into(
            self.points_data['raw_classification'], value, pointdims.CLASSIFICATION_MASK, inplace=True)

    @synthetic.setter
    def synthetic(self, value):
        pointdims.pack_into(self.points_data['raw_classification'], value, pointdims.SYNTHETIC_MASK, inplace=True)

    @key_point.setter
    def key_point(self, value):
        pointdims.pack_into(self.points_data['raw_classification'], value, pointdims.KEY_POINT_MASK, inplace=True)

    @withheld.setter
    def withheld(self, value):
        pointdims.pack_into(self.points_data['raw_classification'], value, pointdims.WITHHELD_MASK, inplace=True)

