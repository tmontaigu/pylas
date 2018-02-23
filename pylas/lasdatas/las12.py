import numpy as np

from .base import LasBase
from .. import vlr, pointdims
from ..compression import (uncompressed_id_to_compressed,
                           compress_buffer,
                           create_laz_vlr)


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

    def to_point_format(self, new_point_format):
        if new_point_format == self.header.point_data_format_id:
            return
        self.points_data.to_point_format(new_point_format)
        self.header.point_data_format_id = new_point_format
        self.header.point_data_record_length = self.points_data.data.dtype.itemsize

    def write_to(self, out_stream, do_compress=False):
        self.update_header()

        if do_compress:
            lazvrl = create_laz_vlr(self.header.point_data_format_id)
            self.vlrs.append(vlr.LasZipVlr(lazvrl.data()))

            self.header.offset_to_point_data = self.header.header_size + self.vlrs.total_size_in_bytes()
            self.header.point_data_format_id = uncompressed_id_to_compressed(self.header.point_data_format_id)
            self.header.number_of_vlr = len(self.vlrs)

            compressed_points = compress_buffer(
                np.frombuffer(self.points_data.data, np.uint8),
                lazvrl.schema,
                self.header.offset_to_point_data,
            )

            print('len of vlrs', self.vlrs.total_size_in_bytes())
            print('offset', self.header.offset_to_point_data)
            print('num vlr', self.header.number_of_vlr)

            self.header.write_to(out_stream)
            self.vlrs.write_to(out_stream)
            assert out_stream.tell() == self.header.offset_to_point_data
            out_stream.write(compressed_points.tobytes())
        else:
            self.header.number_of_vlr = len(self.vlrs)
            self.header.offset_to_point_data = self.header.header_size + self.vlrs.total_size_in_bytes()

            self.header.write_to(out_stream)
            self.vlrs.write_to(out_stream)
            self.points_data.write_to(out_stream)

    def write_to_file(self, filename):
        do_compress = filename.split('.')[-1] == 'laz'
        with open(filename, mode='wb') as out:
            self.write_to(out, do_compress=do_compress)

    def write(self, destination):
        if isinstance(destination, str):
            self.write_to_file(destination)
        else:
            self.write_to(destination)
