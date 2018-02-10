import numpy as np


def point_format_to_dtype(point_format):
    return [(dim_name, dimensions[dim_name]) for dim_name in point_format]


dimensions = {
    'X': 'u4',
    'Y': 'u4',
    'Z': 'u4',
    'intensity': 'u2',
    'jsp': 'u1',
    'classification': 'u1',
    'scan_angle_rank': 'i1',
    'user_data': 'u1',
    'point_source_id': 'u2',
    'gps_time': 'f8',
    'red': 'u2',
    'green': 'u2',
    'blue': 'u2',
}

point_format_0 = (
    'X',
    'Y',
    'Z',
    'intensity',
    'jsp',
    'classification',
    'scan_angle_rank',
    'user_data',
    'point_source_id'
)

point_formats = (
    point_format_0,
    point_format_0 + ('gps_time',),
    point_format_0 + ('red', 'green', 'blue',),
    point_format_0 + ('red', 'green', 'blue', 'gps_time',),
)

point_formats_dtype = tuple(np.dtype(point_format_to_dtype(point_fmt)) for point_fmt in point_formats)
