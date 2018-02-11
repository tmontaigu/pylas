import struct
import ctypes

type_name_to_struct = {
    'uint8': 'B',
    'uint16': 'H',
    'uint32': 'I',
    'uint64': 'Q',
    'int8': 'b',
    'int16': 'h',
    'int32': 'i',
    'int64': 'q',
    'float': 'f',
    'double': 'd',
    'char': 'c',
    'str': 's',
}

type_lengths = {
    'uint8': 1,
    'uint16': 2,
    'uint32': 4,
    'uint64': 8,
    'int8': 1,
    'int16': 2,
    'int32': 4,
    'int64': 8,
    'float': 4,
    'double': 8,
    'char': 1,
    'str': 1,
}

FILE_MAJOR_OFFSET_BYTES = 24


class GlobalEncoding(ctypes.LittleEndianStructure):
    _pack_ = 1
    _fields_ = [
        ('gps_time_type', ctypes.c_uint16, 1),
        ('reserved', ctypes.c_uint16, 15)
    ]

class BinaryReader:
    def __init__(self, stream):
        self.stream = stream

    def read(self, data_type, num=1):
        length = type_lengths[data_type] * num
        if num > 1:
            fmt_str = '{}{}'.format(num, type_name_to_struct[data_type])
        else:
            fmt_str = type_name_to_struct[data_type]
        b = self.stream.read(length)

        # unpack returns a tuple even if the format string
        # has only one element
        if num > 1 and data_type != 'str':
            return struct.unpack(fmt_str, b)
        return struct.unpack(fmt_str, b)[0]

    def read_raw(self, data_type):
        return self.stream.read(type_lengths[data_type])


class RawGUID:
    def __init__(self):
        self.data_1 = 0
        self.data_2 = 0
        self.data_3 = 0
        self.data_4 = b'\x00' * type_lengths['uint8'] * 8

    @classmethod
    def read_from(cls, data_stream):
        guid = cls()
        guid.data_1 = data_stream.read('uint32')
        guid.data_2 = data_stream.read('uint16')
        guid.data_3 = data_stream.read('uint16')
        guid.data_4 = data_stream.read('uint8', num=8)
        return guid


LAS_FILE_SIGNATURE = b'LASF'


# TODO: better defaults
class RawHeader:
    def __init__(self):
        self.file_signature = LAS_FILE_SIGNATURE
        self.file_source_id = 0
        self.global_encoding = 0
        self.guid = RawGUID()
        self.version_major = 1
        self.version_minor = 2
        self.system_identifier = b'\x00' * type_lengths['char'] * 32
        self.generating_software = b'\x00' * type_lengths['char'] * 32
        self.creation_day_of_year = 0
        self.creation_year = 0
        self.header_size = 0
        self.offset_to_point_data = 0
        self.number_of_vlr = 0
        self.point_data_format_id = 0
        self.point_data_record_length = 0
        self.number_of_point_records = 0
        self.number_of_points_by_return = 0
        self.x_scale = 0
        self.y_scale = 0
        self.z_scale = 0
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



    @classmethod
    def read_from(cls, stream):
        data_stream = BinaryReader(stream)
        header = cls()
        header.file_signature = data_stream.read('str', num=4)
        header.file_source_id = data_stream.read('uint16')
        header.global_encoding = GlobalEncoding.from_buffer_copy(data_stream.read_raw('uint16'))
        header.guid = RawGUID.read_from(data_stream)
        header.version_major = data_stream.read('uint8')
        header.version_minor = data_stream.read('uint8')
        header.system_identifier = data_stream.read('str', num=32)
        header.generating_software = data_stream.read('str', num=32)
        header.creation_day_of_year = data_stream.read('uint16')
        header.creation_year = data_stream.read('uint16')
        header.header_size = data_stream.read('uint16')
        header.offset_to_point_data = data_stream.read('uint32')
        header.number_of_vlr = data_stream.read('uint32')
        header.point_data_format_id = data_stream.read('uint8')
        header.point_data_record_length = data_stream.read('uint16')
        header.number_of_point_records = data_stream.read('uint32')
        header.number_of_points_by_return = data_stream.read('uint32', num=5)
        header.x_scale = data_stream.read('double')
        header.y_scale = data_stream.read('double')
        header.z_scale = data_stream.read('double')
        header.x_offset = data_stream.read('double')
        header.y_offset = data_stream.read('double')
        header.z_offset = data_stream.read('double')
        header.x_max = data_stream.read('double')
        header.x_min = data_stream.read('double')
        header.y_max = data_stream.read('double')
        header.y_min = data_stream.read('double')
        header.z_max = data_stream.read('double')
        header.z_min = data_stream.read('double')
        if header.version_major >= 1 and header.version_minor >= 3:
            header.start_of_waveform_data_packet_record = data_stream.read('uint64')
        return header


class Spec:
    def __init__(self, name, type_name, num=1):
        self.name = name,
        if num > 1:
            self.struct_type = "{}{}".format(num, type_name_to_struct[type_name])
        else:
            self.struct_type = type_name_to_struct[type_name]
        self.length = type_lengths[type_name] * num
