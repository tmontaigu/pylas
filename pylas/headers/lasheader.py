import datetime

from . import rawheader
from .. import compression
from .. import pointdims


def convert_raw_header_date(year, day_of_year):
    try:
        return datetime.date(year, 1, 1) + datetime.timedelta(day_of_year - 1)
    except ValueError:
        return None


def to_day_of_year(date):
    return date.timetuple().tm_yday


class Header:
    def __init__(self, version='1.2', point_format=0):
        self.point_count = 0
        self.point_size = pointdims.size_of_point_format(point_format)
        self.scales = (.001, .001, .001)
        self.offsets = (0, 0, 0)
        self.mins = (0, 0, 0)
        self.maxs = (0, 0, 0)
        self.creation_date = datetime.date.today()
        self.generating_software = 'pylas'
        self.point_format = point_format
        self.version = version
        self.is_compressed = False
        self.num_points_by_return = 0
        self.vlr_count = 0

    # TODO Las1.4, offset_to_point_data
    # and other missing fields
    def into_raw(self):
        raw = rawheader.RawHeader()
        raw.number_of_point_records = self.point_count
        raw.number_of_vlr = self.vlr_count
        raw.version_major = int(self.version[0])
        raw.version_minor = int(self.version[2])
        raw.point_data_record_length = self.point_size
        raw.header_size = rawheader.LAS_HEADERS_SIZE[self.version]
        raw.generating_software = self.generating_software.encode() + (32 - len(self.generating_software)) * b'\x00'
        if self.creation_date is not None:
            raw.creation_day_of_year = to_day_of_year(self.creation_date)
            raw.creation_year = self.creation_date.year

        raw.x_max = self.maxs[0]
        raw.y_max = self.maxs[1]
        raw.z_max = self.maxs[2]
        raw.x_min = self.mins[0]
        raw.y_min = self.mins[1]
        raw.z_min = self.mins[2]
        raw.x_offset = self.offsets[0]
        raw.y_offset = self.offsets[1]
        raw.z_offset = self.offsets[2]
        return raw



    @classmethod
    def from_raw(cls, raw_header: rawheader.RawHeader):
        version = '{}.{}'.format(raw_header.version_major, raw_header.version_minor)
        header = cls(version=version, point_format=raw_header.point_data_format_id)
        header.scales = (raw_header.x_scale, raw_header.y_scale, raw_header.z_scale)
        header.mins = (raw_header.x_min, raw_header.y_min, raw_header.z_min)
        header.maxs = (raw_header.x_max, raw_header.y_max, raw_header.z_max)
        header.generating_software = raw_header.generating_software.rstrip(b'\x00').decode()
        header.creation_date = convert_raw_header_date(raw_header.creation_year, raw_header.creation_day_of_year)

        header.is_compressed = compression.is_point_format_compressed(raw_header.point_data_format_id)
        if header.is_compressed:
            header.point_format = compression.compressed_id_to_uncompressed(raw_header.point_data_format_id)
        else:
            header.point_format = raw_header.point_data_format_id

        header.point_count = raw_header.number_of_point_records
        header.num_points_by_return = raw_header.number_of_points_by_return
        if version >= '1.4':
            header.point_count = raw_header.number_of_points_record_
            header.num_points_by_return = raw_header.number_of_points_by_return

        header.point_size = raw_header.point_data_record_length
        header.vlr_count = raw_header.number_of_vlr

        header.raw_header = raw_header
        return header

    @classmethod
    def read_from(cls, stream):
        raw = rawheader.RawHeader.read_from(stream)
        return cls.from_raw(raw)
