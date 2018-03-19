import numpy as np

from pylas.point import record, dims

from .. import vlr
from ..compression import (compress_buffer, create_laz_vlr,
                           uncompressed_id_to_compressed)
from ..headers import rawheader


def scale_dimension(array_dim, scale, offset):
    return (array_dim * scale) + offset


def unscale_dimension(array_dim, scale, offset):
    return (array_dim - offset) / scale


class LasBase(object):
    def __init__(self, *, header=None, vlrs=None, points=None):
        self.__dict__[
            'header'] = header if header is not None else rawheader.RawHeader()
        self.__dict__['vlrs'] = vlrs if vlrs is not None else vlr.VLRList()
        if points is not None:
            if isinstance(points, record.PointRecord):
                self.__dict__['points_data'] = points
            else:
                self.__dict__['points_data'] = record.PackedPointRecord(points)
                self.header.point_data_format_id = self.points_data.point_format_id
        else:
            self.__dict__['points_data'] = record.PackedPointRecord.empty(
                self.header.point_data_format_id)

    @property
    def x(self):
        return scale_dimension(self.X, self.header.x_scale, self.header.x_offset)

    @property
    def y(self):
        return scale_dimension(self.Y, self.header.y_scale, self.header.y_offset)

    @property
    def z(self):
        return scale_dimension(self.Z, self.header.z_scale, self.header.z_offset)

    @x.setter
    def x(self, value):
        self.X = unscale_dimension(
            value, self.header.x_scale, self.header.x_offset)

    @y.setter
    def y(self, value):
        self.Y = unscale_dimension(
            value, self.header.y_scale, self.header.y_offset)

    @z.setter
    def z(self, value):
        self.Z = unscale_dimension(
            value, self.header.z_scale, self.header.z_offset)

    @property
    def points(self):
        return self.points_data.array

    @points.setter
    def points(self, value):
        self.points_data = record.PackedPointRecord(value)

    def __getitem__(self, item):
        return self.points_data[item]

    def __setitem__(self, key, value):
        self.points_data[key] = value

    def __getattr__(self, item):
        return self.points_data[item]

    def __setattr__(self, key, value):
        if key in dims.DIMENSIONS or key in self.points_data.sub_fields_dict:
            self.points_data[key] = value
        else:
            super().__setattr__(key, value)

    def update_header(self):
        self.header.point_data_format_id = self.points_data.point_format_id
        self.header.number_of_point_records = len(self.points_data)
        self.header.number_of_points_records_ = len(self.points_data)
        self.header.point_data_record_length = self.points_data.point_size

        if len(self.points_data) > 0:
            self.header.x_max = self.x.max()
            self.header.y_max = self.y.max()
            self.header.z_max = self.z.max()

            self.header.x_min = self.x.min()
            self.header.y_min = self.y.min()
            self.header.z_min = self.z.min()

    def write_to(self, out_stream, do_compress=False):
        self.update_header()

        if do_compress:
            lazvrl = create_laz_vlr(self.header.point_data_format_id)
            self.vlrs.append(vlr.LasZipVlr(lazvrl.data()))

            self.header.offset_to_point_data = self.header.header_size + \
                self.vlrs.total_size_in_bytes()
            self.header.point_data_format_id = uncompressed_id_to_compressed(
                self.header.point_data_format_id)
            self.header.number_of_vlr = len(self.vlrs)

            compressed_points = compress_buffer(
                np.frombuffer(self.points_data.array, np.uint8),
                lazvrl.schema,
                self.header.offset_to_point_data,
            )

            self.header.write_to(out_stream)
            self.vlrs.write_to(out_stream)
            assert out_stream.tell() == self.header.offset_to_point_data
            out_stream.write(compressed_points.tobytes())
        else:
            self.header.number_of_vlr = len(self.vlrs)
            self.header.offset_to_point_data = self.header.header_size + \
                self.vlrs.total_size_in_bytes()

            self.header.write_to(out_stream)
            self.vlrs.write_to(out_stream)
            self.points_data.write_to(out_stream)

    def write_to_file(self, filename, do_compress=None):
        is_ext_laz = filename.split('.')[-1] == 'laz'
        if is_ext_laz and do_compress is None:
            do_compress = True
        with open(filename, mode='wb') as out:
            self.write_to(out, do_compress=do_compress)

    def write(self, destination, do_compress=None):
        if isinstance(destination, str):
            self.write_to_file(destination)
        else:
            if do_compress is None:
                do_compress = False
            self.write_to(destination, do_compress=do_compress)

    def __repr__(self):
        return 'LasData({}.{}, point fmt: {}, {} points, {} vlrs)'.format(
            self.header.version_major,
            self.header.version_minor,
            self.points_data.point_format_id,
            len(self.points_data),
            len(self.vlrs)
        )
