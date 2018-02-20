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


class LasBase(object):
    def __init__(self, header=None, vlrs=None, points=None):
        self.__dict__['header'] = header if header is not None else rawheader.RawHeader()
        self.__dict__['vlrs'] = vlrs if vlrs is not None else vlr.VLRList()
        if points is not None:
            self.__dict__['np_point_data'] = points
        else:
            self.__dict__['np_point_data'] = pointdata.NumpyPointData.empty(self.header.point_data_format_id)

    @property
    def x(self):
        return scale_dimension(self.X, self.header.x_scale, self.header.x_offset)

    @property
    def y(self):
        return scale_dimension(self.Y, self.header.y_scale, self.header.y_offset)

    @property
    def z(self):
        return scale_dimension(self.Z, self.header.z_scale, self.header.z_offset)

    def __getattr__(self, item):
        return self.np_point_data[item]

    def __setattr__(self, key, value):
        # try to set directly the dimension in the numpy array
        # if it does not exists, search for an existing property-setter
        try:
            self.np_point_data[key] = value
        except ValueError as e:
            prop = getattr(self.__class__, key, None)
            print(key, prop)
            if prop is not None and isinstance(prop, property):
                if prop.fset is None:
                    raise AttributeError("Cannot set {}".format(key))
                print('using property')
                prop.fset(self, value)
            else:
                super().__setattr__(key, value)


class LasData(LasBase):
    def __init__(self, header=None, vlrs=None, points=None):
        super().__init__(header, vlrs, points)
        self.scan_angle_rank = self.np_point_data['scan_angle_rank']
        self.user_data = self.np_point_data['user_data']
        self.point_source_id = self.np_point_data['point_source_id']

    @property
    def return_number(self):
        return pointdims.unpack(self.np_point_data['bit_fields'], pointdims.RETURN_NUMBER_MASK)

    @property
    def number_of_returns(self):
        return pointdims.unpack(self.np_point_data['bit_fields'], pointdims.NUMBER_OF_RETURNS_MASK)

    @property
    def scan_direction_flag(self):
        return pointdims.unpack(self.np_point_data['bit_fields'], pointdims.SCAN_DIRECTION_FLAG_MASK)

    @property
    def edge_of_flight_line(self):
        return pointdims.unpack(self.np_point_data['bit_fields'], pointdims.EDGE_OF_FLIGHT_LINE_MASK)

    @property
    def synthetic(self):
        return pointdims.unpack(self.np_point_data['raw_classification'], pointdims.SYNTHETIC_MASK).astype('bool')

    @property
    def key_point(self):
        return pointdims.unpack(self.np_point_data['raw_classification'], pointdims.KEY_POINT_MASK).astype('bool')

    @property
    def withheld(self):
        return pointdims.unpack(self.np_point_data['raw_classification'], pointdims.WITHHELD_MASK).astype('bool')

    @property
    def classification(self):
        return pointdims.unpack(self.np_point_data['raw_classification'], pointdims.CLASSIFICATION_MASK)

    @number_of_returns.setter
    def number_of_returns(self, value):
        pointdims.pack_into(
            self.np_point_data['bit_fields'], value, pointdims.NUMBER_OF_RETURNS_MASK, inplace=True)

    @scan_direction_flag.setter
    def scan_direction_flag(self, value):
        pointdims.pack_into(
            self.np_point_data['bit_fields'], value, pointdims.SCAN_DIRECTION_FLAG_MASK, inplace=True)

    @edge_of_flight_line.setter
    def edge_of_flight_line(self, value):
        pointdims.pack_into(
            self.np_point_data['bit_fields'], value, pointdims.EDGE_OF_FLIGHT_LINE_MASK, inplace=True)

    @classification.setter
    def classification(self, value):
        pointdims.pack_into(
            self.np_point_data['raw_classification'], value, pointdims.CLASSIFICATION_MASK, inplace=True)

    @synthetic.setter
    def synthetic(self, value):
        pointdims.pack_into(self.np_point_data['raw_classification'], value, pointdims.SYNTHETIC_MASK, inplace=True)

    @key_point.setter
    def key_point(self, value):
        pointdims.pack_into(self.np_point_data['raw_classification'], value, pointdims.KEY_POINT_MASK, inplace=True)

    @withheld.setter
    def withheld(self, value):
        pointdims.pack_into(self.np_point_data['raw_classification'], value, pointdims.WITHHELD_MASK, inplace=True)

    def to_point_format(self, new_point_format):
        if new_point_format == self.header.point_data_format_id:
            return
        self.np_point_data.to_point_format(new_point_format)
        self.header.point_data_format_id = new_point_format
        self.header.point_data_record_length = self.np_point_data.data.dtype.itemsize

    def write_to(self, out_stream, do_compress=False):

        self.header.number_of_point_records = len(self.np_point_data)
        self.header.number_of_points_by_return_ = len(self.np_point_data)

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

    # def __setattr__(self, key, value):
    #     prop = getattr(self.__class__, key, None)
    #     print(key, prop)
    #     if prop is not None and isinstance(prop, property):
    #         if prop.fset is None:
    #             raise AttributeError("Cannot set {}".format(key))
    #         print('using property')
    #         prop.fset(self, value)
    #     else:
    #         super().__setattr__(key, value)

    @classmethod
    def from_file(cls, filename):
        with open(filename, mode='rb') as f:
            return cls.from_file_obj(f)

    @classmethod
    def from_buffer(cls, buf):
        with io.BytesIO(buf) as stream:
            return cls.from_file_obj(stream)

    @classmethod
    def from_file_obj(cls, data_stream):
        header = rawheader.RawHeader.read_from(data_stream)
        assert data_stream.tell() == header.header_size
        vlrs = vlr.VLRList.read_from(data_stream, num_to_read=header.number_of_vlr)

        data_stream.seek(header.offset_to_point_data)
        if is_point_format_compressed(header.point_data_format_id):
            laszip_vlr = vlrs.extract_laszip_vlr()
            if laszip_vlr is None:
                raise ValueError('Could not find Laszip VLR')
            header.point_data_format_id = compressed_id_to_uncompressed(
                header.point_data_format_id)

            # first 8 bytes after header + vlr + evlrs is the offset to the laz chunk table
            data_stream.seek(8, io.SEEK_CUR)
            np_point_data = pointdata.NumpyPointData.from_compressed_stream(
                data_stream,
                header.point_data_format_id,
                header.number_of_point_records,
                laszip_vlr
            )
        else:
            np_point_data = pointdata.NumpyPointData.from_stream(
                data_stream,
                header.point_data_format_id,
                header.number_of_point_records
            )

        return cls(header, vlrs, np_point_data)
