import numpy as np
from pylas.pointdimensions import point_formats_dtype
from pylas.errors import PointFormatNotSupported


class NumpyPointData:
    def __init__(self):
        self.data = None

    def __getitem__(self, item):
        return self.data[item]

    def __setitem__(self, key, value):
        self.data[key] = value

    @classmethod
    def from_stream(cls, stream, point_format_id, count=-1):
        try:
            points_dtype = point_formats_dtype[point_format_id]
        except IndexError:
            raise PointFormatNotSupported("Point format '{}' is not supported".format(
                point_format_id
            ))


        point_data = cls()
        point_data.data = np.fromfile(stream, dtype=points_dtype, count=count)
        return point_data


class PointData:
    def __init__(self, np_point_data):
        self.np_point_data = np_point_data

