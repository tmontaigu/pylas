import datetime

from .rawheader import RawHeader


def convert_raw_header_date(year, day_of_year):
    return datetime.date(year, 1, 1) + datetime.timedelta(day_of_year - 1)


def to_day_of_year(date):
    return date.timetuple().tm_yday


class Header:
    def __init__(self, version='1.2', point_format=0):
        self.point_count = 0
        self.scales = (.01, .01, .01)
        self.offsets = (0, 0, 0)
        self.mins = (0, 0, 0)
        self.maxs = (0, 0, 0)
        self.creation_date = datetime.date.today()
        self.generating_software = 'pylas'
        self.point_format = point_format
        self.version = version

    @classmethod
    def from_raw(cls, raw_header: RawHeader):
        version = '{}.{}'.format(raw_header.version_major, raw_header.version_minor)
        header = cls(version=version, point_format=raw_header.point_data_format_id)
        header.scales = (raw_header.x_scale, raw_header.y_scale, raw_header.z_scale)
        header.mins = (raw_header.x_min, raw_header.y_min, raw_header.z_min)
        header.maxs = (raw_header.x_max, raw_header.y_max, raw_header.z_max)
        header.generating_software = raw_header.generating_software.rstrip(b'\x00').decode()
        header.creation_date = convert_raw_header_date(raw_header.creation_year, raw_header.creation_day_of_year)
