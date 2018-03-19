from abc import ABC, abstractclassmethod, abstractmethod

import numpy as np

from pylas.compression import decompress_buffer
from pylas.point import dims


class PointRecord(ABC):
    @property
    @abstractmethod
    def point_size(self): pass

    @property
    @abstractmethod
    def actual_point_size(self): pass

    @abstractmethod
    def __getitem__(self, item): pass

    @abstractmethod
    def __setitem__(self, key, value): pass

    @abstractmethod
    def __len__(self): pass

    @abstractmethod
    def raw_bytes(self): pass

    @abstractmethod
    def write_to(self, out): pass

    @abstractclassmethod
    def from_stream(cls, stream, point_format_id, count, extra_dims=None): pass

    @abstractclassmethod
    def from_compressed_buffer(
        cls, compressed_buffer, point_format_id, count, laszip_vlr): pass

    @abstractclassmethod
    def empty(cls, point_format_id): pass


class UnpackedPointRecord(PointRecord):
    def __init__(self, data, point_fmt_id=None):
        self.array = data
        self.point_format_id = dims.np_dtype_to_point_format(
            data.dtype, unpacked=True) if point_fmt_id is None else point_fmt_id

    # TODO fix when there are extra dims
    @property
    def point_size(self):
        return dims.get_dtype_of_format_id(self.point_format_id).itemsize

    @property
    def actual_point_size(self):
        return self.array.dtype.itemsize

    def raw_bytes(self):
        return self.array.tobytes()

    def repack_sub_fields(self):
        return dims.repack_sub_fields(self.array, self.point_format_id)

    def write_to(self, out):
        out.write(self.repack_sub_fields().tobytes())

    def __getitem__(self, item):
        return self.array[item]

    def __setitem__(self, key, value):
        if len(value) > len(self.array):
            self.array = np.append(
                self.array,
                np.zeros(len(value) - len(self.array), dtype=self.array.dtype)
            )
        self.array[key] = value

    def __len__(self):
        return self.array.shape[0]

    def to_point_format(self, new_point_format):
        new_dtype = dims.get_dtype_of_format_id(
            new_point_format, unpacked=True)
        new_data = np.zeros_like(self.array, dtype=new_dtype)

        for dim_name in self.array.dtype.names:
            try:
                new_data[dim_name] = self.array[dim_name]
            except ValueError:
                pass
        self.array = new_data
        self.point_format_id = new_point_format

    @classmethod
    def from_stream(cls, stream, point_format_id, count, extra_dims=None):
        points_dtype = dims.get_dtype_of_format_id(
            point_format_id, extra_dims=extra_dims)
        point_data_buffer = bytearray(
            stream.read(count * points_dtype.itemsize))
        data = np.frombuffer(
            point_data_buffer, dtype=points_dtype, count=count)

        point_record = dims.unpack_sub_fields(
            data, point_format_id, extra_dims=extra_dims)

        return cls(point_record, point_format_id)

    @classmethod
    def from_compressed_buffer(cls, compressed_stream, point_format_id, count, laszip_vlr):
        uncompressed = decompress_buffer(
            compressed_stream, point_format_id, count, laszip_vlr)
        uncompressed.flags.writeable = True

        point_record = dims.unpack_sub_fields(uncompressed, point_format_id)

        return cls(point_record, point_format_id)

    @classmethod
    def empty(cls, point_format_id):
        data = np.zeros(0, dtype=dims.get_dtype_of_format_id(
            point_format_id, unpacked=True))
        return cls(data, point_format_id)


class PackedPointRecord(PointRecord):
    def __init__(self, data, point_format_id=None):
        self.array = data
        self.point_format_id = dims.np_dtype_to_point_format(
            data.dtype) if point_format_id is None else point_format_id
        self.sub_fields_dict = dims.get_sub_fields_of_fmt_id(
            self.point_format_id)

    @property
    def point_size(self):
        return self.array.dtype.itemsize

    @property
    def actual_point_size(self):
        return self.point_size

    @property
    def dimensions_names(self):
        return dims.get_dtype_of_format_id(self.point_format_id, unpacked=True).names

    def add_extra_dims(self, type_tuples):
        dype_with_extra_dims = dims.dtype_append(
            self.array.dtype,
            type_tuples
        )
        old_array = self.array
        self.array = np.zeros_like(old_array, dtype=dype_with_extra_dims)
        self.copy_fields_from(old_array)


    def raw_bytes(self):
        return self.array.tobytes()

    def write_to(self, out):
        out.write(self.raw_bytes())

    def __getitem__(self, item):
        try:
            composed_dim, sub_field = self.sub_fields_dict[item]
            return dims.unpack(self.array[composed_dim], sub_field.mask, dtype=sub_field.type)
        except KeyError:
            return self.array[item]

    def __setitem__(self, key, value):
        if len(value) > len(self.array):
            self.array = np.append(
                self.array,
                np.zeros(len(value) - len(self.array), dtype=self.array.dtype)
            )
        try:
            composed_dim, sub_field = self.sub_fields_dict[key]
            dims.pack(
                self.array[composed_dim],
                value,
                sub_field.mask,
                inplace=True
            )
        except KeyError:
            self.array[key] = value

    def __len__(self):
        return self.array.shape[0]

    def copy_fields_from(self, other_record):
        for dim_name in self.dimensions_names:
            try:
                self[dim_name] = other_record[dim_name]
            except ValueError:
                pass

    @classmethod
    def from_point_record(cls, other_point_record, new_point_format):
        array = np.zeros_like(
            other_point_record.array,
            dtype=dims.get_dtype_of_format_id(new_point_format)
        )
        new_record = cls(array, new_point_format)
        new_record.copy_fields_from(other_point_record)
        return new_record

    @classmethod
    def from_stream(cls, stream, point_format_id, count, extra_dims=None):
        points_dtype = dims.get_dtype_of_format_id(
            point_format_id, extra_dims=extra_dims)
        point_data_buffer = bytearray(
            stream.read(count * points_dtype.itemsize))
        data = np.frombuffer(
            point_data_buffer, dtype=points_dtype, count=count)

        return cls(data, point_format_id)

    @classmethod
    def from_compressed_buffer(cls, compressed_buffer, point_format_id, count, laszip_vlr):
        uncompressed = decompress_buffer(
            compressed_buffer, point_format_id, count, laszip_vlr)
        return cls(uncompressed, point_format_id)

    @classmethod
    def empty(cls, point_format_id):
        data = np.zeros(0, dtype=dims.get_dtype_of_format_id(point_format_id))
        return cls(data, point_format_id)
