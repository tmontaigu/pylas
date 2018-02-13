import numpy as np

from pylas.compression import decompress_stream
from pylas.pointdimensions import get_dtype_of_format_id


class NumpyPointData:
    def __init__(self):
        self.data = None

    def __getitem__(self, item):
        return self.data[item]

    def __setitem__(self, key, value):
        self.data[key] = value

    def write_to(self, out):
        out.write(self.data.tobytes())

    @classmethod
    def from_stream(cls, stream, point_format_id, count):
        points_dtype = get_dtype_of_format_id(point_format_id)

        point_data_buffer = stream.read(count * points_dtype.itemsize)
        point_data = cls()
        point_data.data = np.frombuffer(point_data_buffer, dtype=points_dtype, count=count)
        return point_data

    @classmethod
    def from_compressed_stream(cls, compressed_stream, point_format_id, count, laszip_vlr):
        uncompressed = decompress_stream(compressed_stream, point_format_id, count, laszip_vlr)
        return uncompressed
