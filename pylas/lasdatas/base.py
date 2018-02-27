from .. import pointdata
from .. import vlr
import numpy as np
from .. import errors
from ..compression import (uncompressed_id_to_compressed,
                           compress_buffer,
                           create_laz_vlr)
from ..header import rawheader


def scale_dimension(array_dim, scale, offset):
    return (array_dim * scale) + offset


class LasBase(object):

    def __init__(self, header=None, vlrs=None, points=None):
        self.__dict__['header'] = header if header is not None else rawheader.RawHeader()
        self.__dict__['vlrs'] = vlrs if vlrs is not None else vlr.VLRList()
        if points is not None:
            if isinstance(points, pointdata.PointRecord):
                self.__dict__['points_data'] = points
            else:
                self.__dict__['points_data'] = pointdata.UnpackedPointRecord(points)
                self.header.point_data_format_id = self.points_data.point_format_id
        else:
            self.__dict__['points_data'] = pointdata.UnpackedPointRecord.empty(self.header.point_data_format_id)

    @property
    def x(self):
        return scale_dimension(self.X, self.header.x_scale, self.header.x_offset)

    @property
    def y(self):
        return scale_dimension(self.Y, self.header.y_scale, self.header.y_offset)

    @property
    def z(self):
        return scale_dimension(self.Z, self.header.z_scale, self.header.z_offset)

    @property
    def points(self):
        return self.points_data.array

    @points.setter
    def points(self, value):
        self.points_data = pointdata.UnpackedPointRecord(value)

    def __getitem__(self, item):
        return self.points_data[item]

    def __setitem__(self, key, value):
        self.points_data[key] = value

    def __getattr__(self, item):
        return self.points_data[item]

    def __setattr__(self, key, value):
        # Try to forward the call the the point record
        # if fail just do as normal
        try:
            self.points_data[key] = value
        except ValueError:
            super().__setattr__(key, value)

    def update_header(self):
        self.header.point_data_format_id = self.points_data.point_format_id
        self.header.number_of_point_records = len(self.points_data)
        self.header.number_of_points_records_ = len(self.points_data)
        self.header.point_data_record_length = self.points_data.point_size

        self.header.x_max = self.X.max()
        self.header.y_max = self.Y.max()
        self.header.z_max = self.Z.max()

        self.header.x_min = self.X.min()
        self.header.y_min = self.Y.min()
        self.header.z_min = self.Z.min()

    # TODO: check file version compatibility
    def to_point_format(self, new_point_format):
        if new_point_format == self.header.point_data_format_id:
            return
        self.points_data.to_point_format(new_point_format)
        self.header.point_data_format_id = new_point_format
        self.header.point_data_record_length = self.points_data.point_size

    def write_to(self, out_stream, do_compress=False):
        self.update_header()

        if do_compress:
            lazvrl = create_laz_vlr(self.header.point_data_format_id)
            self.vlrs.append(vlr.LasZipVlr(lazvrl.data()))

            self.header.offset_to_point_data = self.header.header_size + self.vlrs.total_size_in_bytes()
            self.header.point_data_format_id = uncompressed_id_to_compressed(self.header.point_data_format_id)
            self.header.number_of_vlr = len(self.vlrs)

            compressed_points = compress_buffer(
                np.frombuffer(self.points_data.array, np.uint8),
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
