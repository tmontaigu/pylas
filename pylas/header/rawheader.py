import ctypes
from collections import namedtuple

from pylas.lasio import BinaryReader, type_lengths, BinaryWriter

FILE_MAJOR_OFFSET_BYTES = 24


class GlobalEncoding(ctypes.LittleEndianStructure):
    _pack_ = 1
    _fields_ = [
        ('gps_time_type', ctypes.c_uint16, 1),
        ('reserved', ctypes.c_uint16, 15)
    ]


class RawGUID:
    def __init__(self):
        self.data_1 = 0
        self.data_2 = 0
        self.data_3 = 0
        self.data_4 = b'\x00' * type_lengths['uint8'] * 8


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
    HeaderField('number_of_points_records', 'uint64', 1),
    HeaderField('number_of_points_by_return', 'uint64', 15),
)


# TODO: better defaults
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
        self.system_identifier = b'\x00' * type_lengths['char'] * 32
        self.generating_software = b'\x00' * type_lengths['char'] * 32
        self.creation_day_of_year = 0
        self.creation_year = 0
        self.header_size = 227
        self.offset_to_point_data = 0
        self.number_of_vlr = 0
        self.point_data_format_id = 0
        self.point_data_record_length = 0
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
        self.number_of_points_record_ = None
        self.number_of_points_by_return_ = None

    def write_to(self, out_stream):
        out_stream = BinaryWriter(out_stream)

        for field in LAS_1_1_HEADER_FIELDS:
            val = getattr(self, field.name)
            out_stream.write(val, field.type, num=field.num)

        if self.version_major >= 1 and self.version_minor >= 3:
            for field in ADDITIONAL_LAS_1_3_FIELDS:
                val = getattr(self, field.name)
                out_stream.write(val, field.type, num=field.num)

        if self.version_major >= 1 and self.version_minor >= 4:
            for field in ADDITIONAL_LAS_1_4_FIELDS:
                val = getattr(self, field.name)
                out_stream.write(val, field.type, num=field.num)

    # FIXME: Maybe we shouldn't continue to read if the file signature is
    # not LASF ans raise an exception
    @classmethod
    def read_from(cls, stream):
        raw_header = cls()
        data_stream = BinaryReader(stream)

        # There must be a way to factorize this nicely
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
