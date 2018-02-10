from pylas import pointdata, header


def scale_dimension(array_dim, scale, offset):
    return (array_dim * scale) + offset


class LasData:
    def __init__(self, data_stream):
        self.data_stream = data_stream
        self.header = header.RawHeader.read_from(self.data_stream)
        self.np_point_data = pointdata.NumpyPointData.from_stream(
            self.data_stream,
            self.header.point_data_format_id,
            self.header.number_of_point_records
        )

    @property
    def X(self):
        return self.np_point_data['X']

    @X.setter
    def X(self, value):
        self.np_point_data['X'] = value

    @property
    def Y(self):
        return self.np_point_data['X']

    @Y.setter
    def Y(self, value):
        self.np_point_data['X'] = value

    @property
    def Z(self):
        return self.np_point_data['X']

    @Z.setter
    def Z(self, value):
        self.np_point_data['X'] = value

    @property
    def x(self):
        return scale_dimension(self.X, self.header.x_scale, self.header.x_offset)

    @property
    def y(self):
        return scale_dimension(self.y, self.header.y_scale, self.header.y_offset)

    @property
    def z(self):
        return scale_dimension(self.z, self.header.z_scale, self.header.z_offset)

    @property
    def intensity(self):
        return self.np_point_data['intensity']

    @intensity.setter
    def intensity(self, value):
        self.np_point_data['intensity'] = value

    @classmethod
    def from_file(cls, filename):
        with open(filename, mode='rb') as f:
            return cls(f)
