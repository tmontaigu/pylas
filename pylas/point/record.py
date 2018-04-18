""" Contains the classes that manages Las PointRecords
Las PointRecords are represented using Numpy's structured arrays,
The PointRecord classes provide a few extra things to manage these arrays
in the context of Las point data
"""
from abc import ABC, abstractclassmethod, abstractmethod

import numpy as np

from . import dims, packing
from ..compression import decompress_buffer


class PointRecord(ABC):
    """ Wraps the numpy structured array contained the points data
    """

    @property
    @abstractmethod
    def point_size(self):
        """ Shall return the point size as that will be written in the header
        """
        pass

    @property
    @abstractmethod
    def actual_point_size(self):
        """ Shall return the actual size in bytes that ta points take in memory
        """
        pass

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


class PackedPointRecord(PointRecord):
    """
    In the PackedPointRecord, fields that are a combinations of many sub-fields (bit-sized fields)
    are still packed together and are only de-packed and re-packed when accessed.

    This uses of less memory than if the sub-fields were unpacked
    However some operations on sub-fields require extra steps:

    return number is a sub-field
    >>> packed_point_record = PackedPointRecord.zeros(0, 10)
    >>> packed_point_record['return_number'][:] = 1
    >>> np.alltrue(packed_point_record == 1)
    False

    >>> packed_point_record = PackedPointRecord.zeros(0, 10)
    >>> rn = packed_point_record['return_number']
    >>> rn[:] = 1
    >>> packed_point_record['return_number'] = rn
    >>> np.alltrue(packed_point_record['return_number'] == 1)
    True
    """

    def __init__(self, data, point_format_id=None):
        self.array = data
        self.point_format_id = dims.np_dtype_to_point_format(
            data.dtype) if point_format_id is None else point_format_id
        self.sub_fields_dict = dims.get_sub_fields_of_fmt_id(self.point_format_id)
        self.dimensions_names = set(dims.get_dtype_of_format_id(self.point_format_id, unpacked=True).names)

        standard_dims = self.dimensions_names.copy()
        standard_dims.update(dims.get_dtype_of_format_id(self.point_format_id, unpacked=False).names)
        self.extra_dimensions_names = set(self.array.dtype.names).difference(standard_dims)

    @property
    def point_size(self):
        """ Returns the point size in bytes taken by each points of the record

        Returns
        -------
        int
            The point size in byte

        """
        return self.array.dtype.itemsize

    @property
    def actual_point_size(self):
        """ Returns the point size in bytes taken by each points of the record

        Returns
        -------
        int
            The point size in byte

        """
        return self.point_size

    def add_extra_dims(self, type_tuples):
        dtype_with_extra_dims = dims.dtype_append(
            self.array.dtype,
            type_tuples
        )
        old_array = self.array
        self.array = np.zeros_like(old_array, dtype=dtype_with_extra_dims)
        self.copy_fields_from(old_array)

    def raw_bytes(self):
        return self.array.tobytes()

    def write_to(self, out):
        out.write(self.raw_bytes())

    def __getitem__(self, item):
        """ Gives access to the underlying numpy array
        Unpack the dimension if item is the name a sub-field
        """
        try:
            composed_dim, sub_field = self.sub_fields_dict[item]
            return packing.unpack(self.array[composed_dim], sub_field.mask, dtype=sub_field.type)
        except KeyError:
            return self.array[item]

    def __setitem__(self, key, value):
        """ Sets elements in the array
        Appends points to all dims when setting an existing dimension to a bigger array
        """
        if len(value) > len(self.array):
            self.array = np.append(
                self.array,
                np.zeros(len(value) - len(self.array), dtype=self.array.dtype)
            )
        try:
            composed_dim, sub_field = self.sub_fields_dict[key]
            packing.pack(
                self.array[composed_dim],
                value,
                sub_field.mask,
                inplace=True
            )
        except KeyError:
            self.array[key] = value

    def __len__(self):
        """ Returns the number of points
        """
        return self.array.shape[0]

    def __repr__(self):
        return '<PackedPointRecord(fmt: {}, len: {}, point size: {})>'.format(
            self.point_format_id, len(self), self.actual_point_size
        )

    def copy_fields_from(self, other_record):
        """ Tries to copy the values of the current dimensions from other_record
        """
        for dim_name in self.dimensions_names:
            try:
                self[dim_name] = other_record[dim_name]
            except ValueError:
                pass

    @classmethod
    def from_point_record(cls, other_point_record, new_point_format):
        """  Construct a new PackedPointRecord from an existing one with the ability to change
        to point format while doing so
        """
        array = np.zeros_like(
            other_point_record.array,
            dtype=dims.get_dtype_of_format_id(new_point_format)
        )
        new_record = cls(array, new_point_format)
        new_record.copy_fields_from(other_point_record)
        return new_record

    @classmethod
    def from_stream(cls, stream, point_format_id, count, extra_dims=None):
        """ Construct the point record by reading the bytes from the stream
        """
        points_dtype = dims.get_dtype_of_format_id(
            point_format_id, extra_dims=extra_dims)
        point_data_buffer = bytearray(
            stream.read(count * points_dtype.itemsize))
        data = np.frombuffer(
            point_data_buffer, dtype=points_dtype, count=count)

        return cls(data, point_format_id)

    @classmethod
    def from_buffer(cls, buffer, point_format_id, count, offset, extra_dims=None):
        points_dtype = dims.get_dtype_of_format_id(
            point_format_id,
            extra_dims=extra_dims
        )
        data = np.frombuffer(
            buffer,
            dtype=points_dtype,
            offset=offset,
            count=count
        )

        return cls(data, point_format_id)

    @classmethod
    def from_compressed_buffer(cls, compressed_buffer, point_format_id, count, laszip_vlr):
        """  Construct the point record by reading and decompressing the points data from
        the input buffer
        """
        uncompressed = decompress_buffer(
            compressed_buffer,
            point_format_id,
            count,
            laszip_vlr
        )
        return cls(uncompressed, point_format_id)

    @classmethod
    def zeros(cls, point_format_id, point_count):
        """ Creates a new point record with all dimensions initialized to zero

        Parameters
        ----------
        point_format_id: int
            The point format id the point record should have
        point_count : int
            The number of point the point record should have

        Returns
        -------
        PackedPointRecord

        """
        data = np.zeros(point_count, dtype=dims.get_dtype_of_format_id(point_format_id))
        return cls(data, point_format_id)

    @classmethod
    def empty(cls, point_format_id):
        """ Creates an empty point record.

        Parameters
        ----------
        point_format_id: int
            The point format id the point record should have

        Returns
        -------
        PackedPointRecord

        """
        return cls.zeros(point_format_id, point_count=0)


class UnpackedPointRecord(PointRecord):
    """
    In the Unpacked Point Record, all the sub-fields are un-packed meaning that they are in their
    own array.
    Because the minimum size for the elements of an array is 8 bits, and sub-fields are only a few bits
    (less than 8) the resulting unpacked array uses more memory, especially if the point format has lots of sub-fields
    """

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
        return packing.repack_sub_fields(self.array, self.point_format_id)

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

        point_record = packing.unpack_sub_fields(
            data, point_format_id, extra_dims=extra_dims)

        return cls(point_record, point_format_id)

    @classmethod
    def from_compressed_buffer(cls, compressed_stream, point_format_id, count, laszip_vlr):
        uncompressed = decompress_buffer(
            compressed_stream, point_format_id, count, laszip_vlr)
        uncompressed.flags.writeable = True

        point_record = packing.unpack_sub_fields(uncompressed, point_format_id)

        return cls(point_record, point_format_id)

    @classmethod
    def empty(cls, point_format_id):
        data = np.zeros(0, dtype=dims.get_dtype_of_format_id(
            point_format_id, unpacked=True))
        return cls(data, point_format_id)
