import io

import numpy as np

from pylas.header import rawheader
from . import pointdata, vlr, pointdims
from .compression import (is_point_format_compressed,
                          compressed_id_to_uncompressed,
                          uncompressed_id_to_compressed,
                          compress_buffer,
                          create_laz_vlr)


def scale_dimension(array_dim, scale, offset):
    return (array_dim * scale) + offset


class LasData:
    def __init__(self, data_stream):
        self.data_stream = data_stream
        self.header = rawheader.RawHeader.read_from(self.data_stream)
        assert data_stream.tell() == self.header.header_size
        self.vlrs = vlr.VLRList.read_from(data_stream, num_to_read=self.header.number_of_vlr)

        self.data_stream.seek(self.header.offset_to_point_data)
        if is_point_format_compressed(self.header.point_data_format_id):
            laszip_vlr = self.vlrs.extract_laszip_vlr()
            if laszip_vlr is None:
                raise ValueError('Could not find Laszip VLR')
            self.header.point_data_format_id = compressed_id_to_uncompressed(
                self.header.point_data_format_id)

            # first 8 bytes after header + vlr + evlrs is the offset to the laz chunk table
            self.save_me = self.data_stream.seek(8, io.SEEK_CUR)
            self.np_point_data = pointdata.NumpyPointData.from_compressed_stream(
                self.data_stream,
                self.header.point_data_format_id,
                self.header.number_of_point_records,
                laszip_vlr
            )
        else:
            self.np_point_data = pointdata.NumpyPointData.from_stream(
                self.data_stream,
                self.header.point_data_format_id,
                self.header.number_of_point_records
            )

        self.X = self.np_point_data['X']
        self.Y = self.np_point_data['Y']
        self.Z = self.np_point_data['Z']
        self.intensity = self.np_point_data['intensity']
        self.scan_angle_rank = self.np_point_data['scan_angle_rank']
        self.user_data = self.np_point_data['user_data']
        self.point_source_id = self.np_point_data['point_source_id']

        self.x = scale_dimension(self.X, self.header.x_scale, self.header.x_offset)
        self.y = scale_dimension(self.Y, self.header.y_scale, self.header.y_offset)
        self.z = scale_dimension(self.Z, self.header.z_scale, self.header.z_offset)

        self.unpack_bit_fields()
        self.unpack_raw_classification()

    @property
    def gps_time(self):
        return self.np_point_data['gps_time']

    @gps_time.setter
    def gps_time(self, value):
        self.np_point_data['gps_time'] = value

    @property
    def red(self):
        return self.np_point_data['red']

    @red.setter
    def red(self, value):
        self.np_point_data['red'] = value

    @property
    def green(self):
        return self.np_point_data['green']

    @green.setter
    def green(self, value):
        self.np_point_data['green'] = value

    @property
    def blue(self):
        return self.np_point_data['blue']

    @blue.setter
    def blue(self, value):
        self.np_point_data['blue'] = value

    def unpack_bit_fields(self):
        # These dimensions have to be repacked together when writing
        self.return_number = pointdims.unpack(
            self.np_point_data['bit_fields'], pointdims.RETURN_NUMBER_MASK)

        self.number_of_returns = pointdims.unpack(
            self.np_point_data['bit_fields'], pointdims.NUMBER_OF_RETURNS_MASK)
        self.scan_direction_flag = pointdims.unpack(
            self.np_point_data['bit_fields'], pointdims.SCAN_DIRECTION_FLAG_MASK)
        self.edge_of_flight_line = pointdims.unpack(
            self.np_point_data['bit_fields'], pointdims.EDGE_OF_FLIGHT_LINE_MASK)

    def unpack_raw_classification(self):
        # Split raw classification
        self.classification = pointdims.unpack(
            self.np_point_data['raw_classification'], pointdims.CLASSIFICATION_MASK)
        self.synthetic = pointdims.unpack(
            self.np_point_data['raw_classification'], pointdims.SYNTHETIC_MASK).astype('bool')
        self.key_point = pointdims.unpack(
            self.np_point_data['raw_classification'], pointdims.KEY_POINT_MASK).astype('bool')
        self.withheld = pointdims.unpack(
            self.np_point_data['raw_classification'], pointdims.WITHHELD_MASK).astype('bool')

    def repack_bit_fields(self):
        self.np_point_data['bit_fields'] = pointdims.repack(
            (self.return_number, self.number_of_returns, self.scan_direction_flag, self.edge_of_flight_line),
            (pointdims.RETURN_NUMBER_MASK,
             pointdims.NUMBER_OF_RETURNS_MASK,
             pointdims.SCAN_DIRECTION_FLAG_MASK,
             pointdims.EDGE_OF_FLIGHT_LINE_MASK)
        )

    def repack_classification(self):
        self.np_point_data['raw_classification'] = pointdims.repack(
            (self.classification, self.synthetic, self.key_point, self.withheld),
            (pointdims.CLASSIFICATION_MASK,
             pointdims.NUMBER_OF_RETURNS_MASK,
             pointdims.SCAN_DIRECTION_FLAG_MASK,
             pointdims.EDGE_OF_FLIGHT_LINE_MASK,)
        )

    def to_point_format(self, new_point_format):
        if new_point_format == self.header.point_data_format_id:
            return
        self.repack_classification()
        self.repack_bit_fields()
        self.np_point_data.to_point_format(new_point_format)
        self.header.point_data_format_id = new_point_format
        self.header.point_data_record_length = self.np_point_data.data.dtype.itemsize
        self.unpack_bit_fields()
        self.unpack_raw_classification()

    def write_to(self, out_stream, do_compress=False):
        self.repack_bit_fields()
        self.repack_classification()

        if do_compress:
            lazvrl = create_laz_vlr(self.header.point_data_format_id)
            self.vlrs.append(vlr.LasZipVlr(lazvrl.data()))

            self.header.offset_to_point_data = self.header.header_size + self.vlrs.total_size_in_bytes()
            self.header.point_data_format_id = uncompressed_id_to_compressed(self.header.point_data_format_id)
            self.header.number_of_vlr = len(self.vlrs)

            compressed_points = compress_buffer(
                np.frombuffer(self.np_point_data.data, np.uint8),
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
            self.np_point_data.write_to(out_stream)

    def write_to_file(self, filename):
        do_compress = filename.split('.')[-1] == 'laz'
        with open(filename, mode='wb') as out:
            self.write_to(out, do_compress=do_compress)

    def write(self, destination):
        if isinstance(destination, str):
            self.write_to_file(destination)
        else:
            self.write_to(destination)

    @classmethod
    def open(cls, source):
        if isinstance(source, bytes):
            return cls.from_buffer(source)
        elif isinstance(source, str):
            return cls.from_file(source)
        else:
            return cls(source)

    @classmethod
    def from_file(cls, filename):
        with open(filename, mode='rb') as f:
            return cls(f)

    @classmethod
    def from_buffer(cls, buf):
        with io.BytesIO(buf) as stream:
            return cls(stream)
