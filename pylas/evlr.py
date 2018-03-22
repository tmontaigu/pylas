from collections import namedtuple
import ctypes


class EVLRHeader(ctypes.LittleEndianStructure):
    _fields_ = [
        ('_reserved', ctypes.c_uint16),
        ('user_id', ctypes.c_char * 16),
        ('record_id', ctypes.c_uint16),
        ('record_length_after_header', ctypes.c_uint64),
        ('description', ctypes.c_char * 32)
    ]


EVLR_HEADER_SIZE = ctypes.sizeof(EVLRHeader)


class RawEVLR:
    def __init__(self):
        self.header = EVLRHeader()
        self.record_data = b''

    @classmethod
    def read_from(cls, data_stream):
        raw_evlr = cls()
        raw_evlr.header = EVLRHeader.from_buffer(bytearray(data_stream.read(EVLR_HEADER_SIZE)))
        raw_evlr.record_data = data_stream.read(raw_evlr.header.record_length_after_header)
        return raw_evlr

    def write_to(self, out):
        out.write(bytes(self.header))
        out.write(self.record_data)

    def __repr__(self):
        return 'RawEVLR(user_id: {}, record_id: {}, record_length_after_header: {}'.format(
            self.header.user_id, self.header.record_id, self.header.record_length_after_header
        )


class EVLR:
    def __init__(self):
        pass
