import io

import numpy as np

from pylas.header import rawheader
from . import pointdata, vlr, pointdimensions
from .compression import is_point_format_compressed, compressed_id_to_uncompressed, compress_buffer


def scale_dimension(array_dim, scale, offset):
    return (array_dim * scale) + offset


class LasData:
    def __init__(self, data_stream):
        self.data_stream = data_stream
        self.header = rawheader.RawHeader.read_from(self.data_stream)
        self.vlrs = vlr.VLRList.read_from(data_stream, num_to_read=self.header.number_of_vlr)
        print("fmt:", self.header.point_data_format_id)

        if is_point_format_compressed(self.header.point_data_format_id):
            laszip_vlr = self.vlrs.find_laszip_vlr()
            if laszip_vlr is None:
                print(self.vlrs)
                raise ValueError('Could not find Laszip VLR')

            # first 8 bytes after header + vlr + evlrs are laszip data
            self.save_me = self.data_stream.read(8)
            self.np_point_data = pointdata.NumpyPointData.from_compressed_stream(
                self.data_stream,
                compressed_id_to_uncompressed(self.header.point_data_format_id),
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

        # These dimensions have to be repacked together when writing
        self.return_number = pointdimensions.bit_transform(
            self.np_point_data['bit_fields'],
            pointdimensions.RETURN_NUMBER_LOW_BIT,
            pointdimensions.RETURN_NUMBER_HIGH_BIT
        )

        self.number_of_returns = pointdimensions.bit_transform(
            self.np_point_data['bit_fields'],
            pointdimensions.NUMBER_OF_RETURNS_LOW_BIT,
            pointdimensions.NUMBER_OF_RETURNS_HIGH_BIT
        )

        self.scan_direction_flag = pointdimensions.bit_transform(
            self.np_point_data['bit_fields'],
            pointdimensions.SCAN_DIRECTION_FLAG_LOW_BIT,
            pointdimensions.SCAN_DIRECTION_FLAG_HIGH_BIT
        )

        self.edge_of_flight_line = pointdimensions.bit_transform(
            self.np_point_data['bit_fields'],
            pointdimensions.EDGE_OF_FLIGHT_LINE_LOW_BIT,
            pointdimensions.EDGE_OF_FLIGHT_LINE_HIGH_BIT
        )

        # Split raw classification
        self.classification = pointdimensions.bit_transform(
            self.np_point_data['raw_classification'],
            pointdimensions.CLASSIFICATION_LOW_BIT,
            pointdimensions.CLASSIFICATION_HIGH_BIT
        )

        self.synthetic = pointdimensions.bit_transform(
            self.np_point_data['raw_classification'],
            pointdimensions.SYNTHETIC_LOW_BIT,
            pointdimensions.SYNTHETIC_HIGH_BIT,
        ).astype('bool')

        self.key_point = pointdimensions.bit_transform(
            self.np_point_data['raw_classification'],
            pointdimensions.KEY_POINT_LOW_BIT,
            pointdimensions.KEY_POINT_HIGH_BIT
        ).astype('bool')

        self.withheld = pointdimensions.bit_transform(
            self.np_point_data['raw_classification'],
            pointdimensions.WITHHELD_LOW_BIT,
            pointdimensions.WITHHELD_HIGH_BIT
        ).astype('bool')

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

    def write_to(self, out_stream, do_compress=False):
        if do_compress:
            print("Data fmt", self.header.point_data_format_id)
            self.header.offset_to_point_data = self.header.header_size + 52 + 54
            print('offset', self.header.offset_to_point_data)
            self.header.point_data_format_id = 131
            self.header.number_of_vlr = 1
            self.header.write_to(out_stream)
            # self.vlrs.vlrs = [_vlr for _vlr in self.vlrs if not _vlr.is_laszip_vlr()]
            # self.vlrs.write_to(out_stream)

            c, vlr_data = compress_buffer(
                np.frombuffer(self.np_point_data.data, np.uint8),
                0,
                self.header.number_of_point_records,
                self.header.offset_to_point_data
            )
            laszip_vlr = vlr.LasZipVlr(vlr_data.tobytes())
            print(laszip_vlr)
            print('a', out_stream.tell())
            laszip_vlr.into_raw().write_to(out_stream)
            print('b', out_stream.tell())
            out_stream.write(c.tobytes())
        else:
            self.header.point_data_format_id = compressed_id_to_uncompressed(self.header.point_data_format_id)
            self.header.write_to(out_stream)
            print(self.header.header_size)
            self.vlrs.write_to(out_stream)
            self.np_point_data.write_to(out_stream, do_compress=do_compress)

    @classmethod
    def from_file(cls, filename):
        with open(filename, mode='rb') as f:
            return cls(f)

    @classmethod
    def from_buffer(cls, buf):
        with io.BytesIO(buf) as stream:
            return cls(stream)
