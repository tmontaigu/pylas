import numpy as np

from .compression import decompress_buffer
from .pointdims import get_dtype_of_format_id, np_dtype_to_point_format


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
        return self.array.dtype.itemsize

    def to_point_format(self, new_point_format):
        new_dtype = get_dtype_of_format_id(new_point_format)

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

    def write_to(self, out):
        out.write(self.raw_bytes())

    @classmethod
    def from_stream(cls, stream, point_format_id, count, extra_dims=None):
        points_dtype = get_dtype_of_format_id(point_format_id, extra_dims=extra_dims)

        point_data_buffer = bytearray(stream.read(count * points_dtype.itemsize))
        data = np.frombuffer(point_data_buffer, dtype=points_dtype, count=count)
        return cls(data, point_format_id)

    @classmethod
    def from_compressed_stream(cls, compressed_stream, point_format_id, count, laszip_vlr):
        uncompressed = decompress_buffer(compressed_stream, point_format_id, count, laszip_vlr)
        uncompressed.flags.writeable = True
        return cls(uncompressed, point_format_id)

    @classmethod
    def empty(cls, point_format_id):
        data = np.zeros(0, dtype=get_dtype_of_format_id(point_format_id))
        return cls(data, point_format_id)
