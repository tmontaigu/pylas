import numpy as np

from pylas.errors import PointFormatNotSupported
from pylas.pointdimensions import point_formats_dtype


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
        try:
            points_dtype = point_formats_dtype[point_format_id]
        except IndexError:
            raise PointFormatNotSupported("Point format '{}' is not supported".format(
                point_format_id
            ))

        point_data_buffer = stream.read(count * points_dtype.itemsize)
        point_data = cls()
        point_data.data = np.frombuffer(point_data_buffer, dtype=points_dtype, count=count)
        return point_data
