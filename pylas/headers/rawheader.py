import ctypes
import datetime
from collections import namedtuple

from pylas.lasio import BinaryReader, BinaryWriter, type_lengths
from ..point import dims


class GlobalEncoding(ctypes.LittleEndianStructure):
    _pack_ = 1
    _fields_ = [
        ('gps_time_type', ctypes.c_uint16, 1),
        ('waveform_internal', ctypes.c_uint16, 1),  # 1.3
        ('waveform_external', ctypes.c_uint16, 1),  # 1.3
        ('synthetic_return_numbers', ctypes.c_uint16, 1),  # 1.3
        ('wkt', ctypes.c_uint16, 1),  # 1.4
        ('reserved', ctypes.c_uint16, 11),
    ]


class RawHeader1_1(ctypes.LittleEndianStructure):
    _pack_ = 1
    _fields_ = [
        ('file_signature', ctypes.c_char * 4),
        ('file_source_id', ctypes.c_uint16),
        ('global_encoding', GlobalEncoding),
        ('guid_data_1', ctypes.c_uint32),
        ('guid_data_2', ctypes.c_uint16),
        ('guid_data_3', ctypes.c_uint16),
        ('guid_data_4', ctypes.c_uint8 * 8),
        ('version_major', ctypes.c_uint8),
        ('version_minor', ctypes.c_uint8),
        ('system_identifier', ctypes.c_char * 32),
        ('generating_software', ctypes.c_char * 32),
        ('creation_day_of_year', ctypes.c_uint16),
        ('creation_year', ctypes.c_uint16),
        ('header_size', ctypes.c_uint16),
        ('offset_to_point_data', ctypes.c_uint32),
        ('number_of_vlr', ctypes.c_uint32),
        ('point_data_format_id', ctypes.c_uint8),
        ('point_data_record_length', ctypes.c_uint16),
        ('legacy_number_of_point_records', ctypes.c_uint32),
        ('legacy_number_of_point_by_return', ctypes.c_uint32 * 5),
        ('x_scale', ctypes.c_double),
        ('y_scale', ctypes.c_double),
        ('z_scale', ctypes.c_double),
        ('x_offset', ctypes.c_double),
        ('y_offset', ctypes.c_double),
        ('z_offset', ctypes.c_double),
        ('x_max', ctypes.c_double),
        ('x_min', ctypes.c_double),
        ('y_max', ctypes.c_double),
        ('y_min', ctypes.c_double),
        ('z_max', ctypes.c_double),
        ('z_min', ctypes.c_double),
    ]

    @property
    def number_of_point_records(self):
        return self.legacy_number_of_point_records

    @number_of_point_records.setter
    def number_of_point_records(self, value):
        self.legacy_number_of_point_records = value

    @property
    def version(self):
        return "{}.{}".format(self.version_major, self.version_minor)

    @version.setter
    def version(self, new_version):
        try:
            self.header_size = LAS_HEADERS_SIZE[str(new_version)]
        except KeyError:
            raise ValueError('{} is not a valid las header version')
        self.version_major, self.version_minor = map(
            int, new_version.split('.'))

    @property
    def date(self):
        try:
            return datetime.date(self.creation_year, 1, 1) + datetime.timedelta(self.creation_day_of_year - 1)
        except ValueError:
            return None

    @date.setter
    def date(self, date):
        self.creation_year = date.year
        self.creation_day_of_year = date.timetuple().tm_yday


    def write_to(self, out_stream):
        out_stream.write(bytes(self))


class RawHeader1_3(RawHeader1_1):
    _fields_ = [
        ('start_of_waveform_data_packet_record', ctypes.c_uint64)
    ]


class RawHeader1_4(RawHeader1_3):
    _fields_ = [
        ('start_of_first_evlr', ctypes.c_uint64),
        ('number_of_evlr', ctypes.c_uint32),
        ('number_of_point_records', ctypes.c_uint64),
        ('number_of_points_by_return', ctypes.c_uint64 * 15)
    ]


class HeaderFactory:
    version_to_header = {
        '1.1': RawHeader1_1,
        '1.2': RawHeader1_1,
        '1.3': RawHeader1_3,
        '1.4': RawHeader1_4
    }
    offset_to_major_version = RawHeader1_1.version_major.offset

    def read_from_stream(self, stream):
        old_pos = stream.tell()
        stream.seek(self.offset_to_major_version)
        major = int.from_bytes(stream.read(ctypes.sizeof(ctypes.c_uint8)), 'little')
        minor = int.from_bytes(stream.read(ctypes.sizeof(ctypes.c_uint8)), 'little')
        version = '{}.{}'.format(major, minor)

        header_class = self.version_to_header[version]
        stream.seek(old_pos)
        return header_class.from_buffer(bytearray(stream.read(ctypes.sizeof(header_class))))


LAS_FILE_SIGNATURE = b'LASF'

HeaderField = namedtuple('HeaderField', ('name', 'type', 'num'))

LAS_1_1_HEADER_FIELDS = (
    HeaderField('file_signature', 'str', 4),
    HeaderField('file_source_id', 'uint16', 1),
    HeaderField('reserved', 'uint16', 1),
    HeaderField('guid_data_1', 'uint32', 1),
    HeaderField('guid_data_2', 'uint16', 1),
    HeaderField('guid_data_3', 'uint16', 1),
    HeaderField('guid_data_4', 'uint8', 8),
    HeaderField('version_major', 'uint8', 1),
    HeaderField('version_minor', 'uint8', 1),
    HeaderField('system_identifier', 'str', 32),
    HeaderField('generating_software', 'str', 32),
    HeaderField('creation_day_of_year', 'uint16', 1),
    HeaderField('creation_year', 'uint16', 1),
    HeaderField('header_size', 'uint16', 1),
    HeaderField('offset_to_point_data', 'uint32', 1),
    HeaderField('number_of_vlr', 'uint32', 1),
    HeaderField('point_data_format_id', 'uint8', 1),
    HeaderField('point_data_record_length', 'uint16', 1),
    HeaderField('number_of_point_records', 'uint32', 1),
    HeaderField('number_of_points_by_return', 'uint32', 5),
    HeaderField('x_scale', 'double', 1),
    HeaderField('y_scale', 'double', 1),
    HeaderField('z_scale', 'double', 1),
    HeaderField('x_offset', 'double', 1),
    HeaderField('y_offset', 'double', 1),
    HeaderField('z_offset', 'double', 1),
    HeaderField('x_max', 'double', 1),
    HeaderField('x_min', 'double', 1),
    HeaderField('y_max', 'double', 1),
    HeaderField('y_min', 'double', 1),
    HeaderField('z_max', 'double', 1),
    HeaderField('z_min', 'double', 1),
)

ADDITIONAL_LAS_1_3_FIELDS = (
    HeaderField('start_of_waveform_data_packet_record', 'uint64', 1),
)

ADDITIONAL_LAS_1_4_FIELDS = (
    HeaderField('start_of_first_evlr', 'uint64', 1),
    HeaderField('number_of_evlr', 'uint32', 1),
    HeaderField('number_of_point_records', 'uint64', 1),
    HeaderField('number_of_points_by_return_', 'uint64', 15),
)


def size_of(header_fields):
    return sum(type_lengths[field.type] * field.num for field in header_fields)


LAS_1_1_HEADER_SIZE = size_of(LAS_1_1_HEADER_FIELDS)
LAS_HEADERS_SIZE = {
    '1.1': LAS_1_1_HEADER_SIZE,
    '1.2': LAS_1_1_HEADER_SIZE,
    '1.3': LAS_1_1_HEADER_SIZE + size_of(ADDITIONAL_LAS_1_3_FIELDS),
    '1.4': LAS_1_1_HEADER_SIZE + size_of(ADDITIONAL_LAS_1_3_FIELDS) + size_of(ADDITIONAL_LAS_1_4_FIELDS)
}

PROJECT_NAME = b'pylas'


# TODO: Should ctypes also be used for Las headers ?
class RawHeader:
    def __init__(self):
        self.file_signature = LAS_FILE_SIGNATURE
        self.file_source_id = 0
        self.reserved = 0  # global_encoding
        self.guid_data_1 = 0
        self.guid_data_2 = 0
        self.guid_data_3 = 0
        self.guid_data_4 = b'\x00' * type_lengths['char'] * 8
        self.version_major = 1
        self.version_minor = 2
        self._system_identifier = b'\x00' * type_lengths['char'] * 32
        self.generating_software = PROJECT_NAME + b'\x00' * (32 - len(PROJECT_NAME))
        self.creation_day_of_year = 0
        self.creation_year = 0
        self.header_size = LAS_HEADERS_SIZE[self.version]
        self.offset_to_point_data = self.header_size
        self.number_of_vlr = 0
        self.point_data_format_id = 0
        self.point_data_record_length = dims.size_of_point_format(self.point_data_format_id)
        self.number_of_point_records = 0  # Legacy-ed in 1.4
        self.number_of_points_by_return = (0, 0, 0, 0, 0)  # Legacy-ed in 1.4
        self.x_scale = 0.01
        self.y_scale = 0.01
        self.z_scale = 0.01
        self.x_offset = 0
        self.y_offset = 0
        self.z_offset = 0
        self.x_max = 0
        self.x_min = 0
        self.y_max = 0
        self.y_min = 0
        self.z_max = 0
        self.z_min = 0
        # Added in las 1.3
        self.start_of_waveform_data_packet_record = None
        # Added in las 1.4
        self.start_of_first_evlr = None
        self.number_of_evlr = None
        # This 1 member won't be read nor written
        # because in the HEADER_FIELDS definitions
        # it has the same name in 1.2 header & 1.4 additional header
        self.number_of_points_record_ = None
        self.number_of_points_by_return_ = (0,) * 15

        self.date = datetime.date.today()

    @property
    def system_identifier(self):
        return self._system_identifier

    @system_identifier.setter
    def system_identifier(self, value):
        if len(value) > 32:
            raise ValueError
        self._system_identifier = value + (32 - len(value)) * b'\x00'

    @property
    def version(self):
        return "{}.{}".format(self.version_major, self.version_minor)

    @version.setter
    def version(self, new_version):
        try:
            self.header_size = LAS_HEADERS_SIZE[str(new_version)]
        except KeyError:
            raise ValueError('{} is not a valid las header version')
        self.version_major, self.version_minor = map(
            int, new_version.split('.'))

    @property
    def date(self):
        try:
            return datetime.date(self.creation_year, 1, 1) + datetime.timedelta(self.creation_day_of_year - 1)
        except ValueError:
            return None

    @date.setter
    def date(self, date):
        self.creation_year = date.year
        self.creation_day_of_year = date.timetuple().tm_yday

    def write_to(self, out_stream):
        out_stream = BinaryWriter(out_stream)

        for field in LAS_1_1_HEADER_FIELDS:
            val = getattr(self, field.name)
            out_stream.write_field(field, val)

        if self.version_major >= 1 and self.version_minor >= 3:
            for field in ADDITIONAL_LAS_1_3_FIELDS:
                val = getattr(self, field.name)
                out_stream.write_field(field, val)

        if self.version_major >= 1 and self.version_minor >= 4:
            for field in ADDITIONAL_LAS_1_4_FIELDS:
                val = getattr(self, field.name)
                out_stream.write_field(field, val)

    # FIXME: Maybe we shouldn't continue to read if the file signature is
    # not LASF ans raise an exception
    @classmethod
    def read_from(cls, stream):
        raw_header = cls()
        data_stream = BinaryReader(stream)

        for field in LAS_1_1_HEADER_FIELDS:
            val = data_stream.read(field.type, num=field.num)
            setattr(raw_header, field.name, val)

        if raw_header.version_major >= 1 and raw_header.version_minor >= 3:
            for field in ADDITIONAL_LAS_1_3_FIELDS:
                val = data_stream.read(field.type, num=field.num)
                setattr(raw_header, field.name, val)

        if raw_header.version_major >= 1 and raw_header.version_minor >= 4:
            for field in ADDITIONAL_LAS_1_4_FIELDS:
                val = data_stream.read(field.type, num=field.num)
                setattr(raw_header, field.name, val)

        return raw_header
