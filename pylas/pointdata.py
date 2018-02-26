import numpy as np

from . import pointdims
from .compression import decompress_buffer
from .pointdims import get_dtype_of_format_id, np_dtype_to_point_format, UNPACKED_POINT_FORMATS_DTYPES, SUB_FIELDS


class NumpyPointData:
    def __init__(self, data, point_fmt_id=None):
        self.array = data
        self.point_format_id = np_dtype_to_point_format(data.dtype) if point_fmt_id is None else point_fmt_id

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

    @property
    def point_size(self):
        return get_dtype_of_format_id(self.point_format_id).itemsize

    def to_point_format(self, new_point_format):
        new_dtype = UNPACKED_POINT_FORMATS_DTYPES[new_point_format]

        new_data = np.zeros_like(self.array, dtype=new_dtype)

        for dim_name in self.array.dtype.names:
            try:
                new_data[dim_name] = self.array[dim_name]
            except ValueError:
                pass
        self.array = new_data
        self.point_format_id = new_point_format

    def raw_bytes(self):
        return self.array.tobytes()

    def repack_sub_fields(self):
        repacked_array = np.zeros_like(self.array, get_dtype_of_format_id(self.point_format_id))

        for dim_name in repacked_array.dtype.names:
            if dim_name in SUB_FIELDS:
                for sub_field in SUB_FIELDS[dim_name]:
                    try:
                        pointdims.pack_into(
                            repacked_array[dim_name],
                            self.array[sub_field.name],
                            sub_field.mask,
                            inplace=True
                        )
                    except OverflowError as e:
                        raise OverflowError("Error repacking {} into {}: {}".format(sub_field.name, dim_name, e))
            else:
                repacked_array[dim_name] = self.array[dim_name]
        return repacked_array

    def write_to(self, out):
        out.write(self.repack_sub_fields().tobytes())

    @classmethod
    def from_stream(cls, stream, point_format_id, count, extra_dims=None):
        points_dtype = get_dtype_of_format_id(point_format_id, extra_dims=extra_dims)
        point_data_buffer = bytearray(stream.read(count * points_dtype.itemsize))
        data = np.frombuffer(point_data_buffer, dtype=points_dtype, count=count)

        dtype = UNPACKED_POINT_FORMATS_DTYPES[point_format_id]
        point_record = np.zeros_like(data, dtype)

        unpack_sub_fields(data, point_record)

        return cls(point_record, point_format_id)

    @classmethod
    def from_compressed_stream(cls, compressed_stream, point_format_id, count, laszip_vlr):
        uncompressed = decompress_buffer(compressed_stream, point_format_id, count, laszip_vlr)
        uncompressed.flags.writeable = True

        dtype = UNPACKED_POINT_FORMATS_DTYPES[point_format_id]
        point_record = np.zeros_like(uncompressed, dtype)
        unpack_sub_fields(uncompressed, point_record)

        return cls(point_record, point_format_id)

    @classmethod
    def empty(cls, point_format_id):
        data = np.zeros(0, dtype= UNPACKED_POINT_FORMATS_DTYPES[point_format_id])
        return cls(data, point_format_id)


def unpack_sub_fields(data, point_record):
    for dim_name in data.dtype.names:
        if dim_name in SUB_FIELDS:
            for sub_field in SUB_FIELDS[dim_name]:
                point_record[sub_field.name] = pointdims.unpack(data[dim_name], sub_field.mask)
        else:
            point_record[dim_name] = data[dim_name]
