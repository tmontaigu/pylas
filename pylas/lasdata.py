from pylas import pointdata, header, vlr
from pylas import pointdimensions


def scale_dimension(array_dim, scale, offset):
    return (array_dim * scale) + offset


class LasData:
    def __init__(self, data_stream):
        self.data_stream = data_stream
        self.header = header.RawHeader.read_from(self.data_stream)
        self.vlrs = []
        for _ in range(self.header.number_of_vlr):
            self.vlrs.append(vlr.RawVLR.read_from(self.data_stream))
        self.np_point_data = pointdata.NumpyPointData.from_stream(
            self.data_stream,
            self.header.point_data_format_id,
            self.header.number_of_point_records
        )

        # These dimensions have to be repacked together when writing
        self.return_number = pointdimensions.bit_transform(
            self.np_point_data['bit_fields'],
            pointdimensions.RETURN_NUMBER_LOW_BIT,
            pointdimensions.RETURN_NUMBER_HIGH_BIT
        )

        self.number_of_returns = pointdimensions.bit_transform(
            self.np_point_data['bit_fields'],
            pointdimensions.NUMBER_OF_RETURNS_LOW_BIT,
            pointdimensions.NUMBER_OF_RETURNS_HIGH_BIT
        )

        self.scan_direction_flag = pointdimensions.bit_transform(
            self.np_point_data['bit_fields'],
            pointdimensions.SCAN_DIRECTION_FLAG_LOW_BIT,
            pointdimensions.SCAN_DIRECTION_FLAG_HIGH_BIT
        )

        self.edge_of_flight_line = pointdimensions.bit_transform(
            self.np_point_data['bit_fields'],
            pointdimensions.EDGE_OF_FLIGHT_LINE_LOW_BIT,
            pointdimensions.EDGE_OF_FLIGHT_LINE_HIGH_BIT
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

    @property
    def classification(self):
        return self.np_point_data['classification']

    @property
    def scan_angle_rank(self):
        return self.np_point_data['scan_angle_rank']

    @scan_angle_rank.setter
    def scan_angle_rank(self, value):
        self.np_point_data['scan_angle_rank'] = value

    @property
    def user_data(self):
        return self.np_point_data['user_data']

    @user_data.setter
    def user_data(self, value):
        self.np_point_data['user_data'] = value

    @property
    def point_source_id(self):
        return self.np_point_data['point_source_id']

    @point_source_id.setter
    def point_source_id(self, value):
        self.np_point_data['point_source_id'] = value

    @classmethod
    def from_file(cls, filename):
        with open(filename, mode='rb') as f:
            return cls(f)
