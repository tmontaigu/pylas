import numpy as np

from .compression import decompress_stream
from .pointdims import get_dtype_of_format_id


class NumpyPointData:
    def __init__(self, data):
        self.data = data

    def __getitem__(self, item):
        return self.data[item]

    def __setitem__(self, key, value):
        self.data[key] = value

    def __len__(self):
        return self.data.shape[0]

    def to_point_format(self, new_point_format):
        new_dtype = get_dtype_of_format_id(new_point_format)

        new_data = np.zeros_like(self.data, dtype=new_dtype)

        for dim_name in self.data.dtype.names:
            try:
                new_data[dim_name] = self.data[dim_name]
            except ValueError:
                pass
        self.data = new_data



    def write_to(self, out):
        raw_bytes = self.data.tobytes()
        out.write(raw_bytes)

    @classmethod
    def from_stream(cls, stream, point_format_id, count):
        points_dtype = get_dtype_of_format_id(point_format_id)

        point_data_buffer = stream.read(count * points_dtype.itemsize)
        data = np.frombuffer(point_data_buffer, dtype=points_dtype, count=count)
        data.flags.writeable = True
        return cls(data)

    @classmethod
    def from_compressed_stream(cls, compressed_stream, point_format_id, count, laszip_vlr):
        uncompressed = decompress_stream(compressed_stream, point_format_id, count, laszip_vlr)
        uncompressed.flags.writeable = True
        return cls(uncompressed)
