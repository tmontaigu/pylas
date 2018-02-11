import struct

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


class BinaryReader:
    def __init__(self, stream, endianness='little'):
        self.stream = stream
        self.endian = '<' if endianness == 'little' else '>'

    def read(self, data_type, num=1):
        if num == 0:
            return b''

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


class BinaryWriter:
    def __init__(self, stream):
        self.stream = stream

    def write(self, values, data_type, num=1):
        if num > 1:
            fmt_str = '{}{}'.format(num, type_name_to_struct[data_type])
        else:
            fmt_str = type_name_to_struct[data_type]

        if num > 1 and data_type != 'str':
            b = struct.pack(fmt_str, *values)
        else:
            b = struct.pack(fmt_str, values)
        return self.stream.write(b)
