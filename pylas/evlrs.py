import ctypes
import logging

from .vlrs import rawvlr, vlrlist, known

logger = logging.getLogger(__name__)


class EVLRHeader(ctypes.LittleEndianStructure):
    _pack_ = 1
    _fields_ = [
        ("_reserved", ctypes.c_uint16),
        ("user_id", ctypes.c_char * 16),
        ("record_id", ctypes.c_uint16),
        ("record_length_after_header", ctypes.c_uint64),
        ("description", ctypes.c_char * 32),
    ]


EVLR_HEADER_SIZE = ctypes.sizeof(EVLRHeader)


class RawEVLR:
    def __init__(self):
        self.header = EVLRHeader()
        self._record_data = b""

    @property
    def record_data(self):
        return self._record_data

    @record_data.setter
    def record_data(self, value):
        self._record_data = value
        self.header.record_length_after_header = len(value)

    @classmethod
    def read_from(cls, data_stream):
        raw_evlr = cls()
        raw_evlr.header = EVLRHeader.from_buffer(
            bytearray(data_stream.read(EVLR_HEADER_SIZE))
        )
        raw_evlr.record_data = data_stream.read(
            raw_evlr.header.record_length_after_header
        )
        return raw_evlr

    def size_in_bytes(self):
        return EVLR_HEADER_SIZE + self.header.record_length_after_header

    def write_to(self, out):
        out.write(bytes(self.header))
        out.write(self.record_data)

    def __eq__(self, other):
        return (
            self.header.user_id == other.header.user_id
            and self.header.record_id == other.header.record_id
            and self.header.description == other.header.description
            and self.record_data == other.record_data
        )

    def __repr__(self):
        return "<RawEVLR(user_id: {}, record_id: {}, record_length_after_header: {})>".format(
            self.header.user_id,
            self.header.record_id,
            self.header.record_length_after_header,
        )


class EVLR(rawvlr.VLR):
    pass


def evlr_factory(raw):
    return known.vlr_factory(raw)


class RawEVLRList(vlrlist.RawVLRList):
    @classmethod
    def from_list(cls, vlrs):
        raw_vlrs = cls()
        for vlr in vlrs:
            raw = RawEVLR()
            raw.header.user_id = vlr.user_id.encode("utf8")
            raw.header.description = vlr.description.encode("utf8")
            raw.header.record_id = vlr.record_id
            raw.record_data = vlr.record_data_bytes()
            raw_vlrs.append(raw)
        return raw_vlrs


class EVLRList(vlrlist.VLRList):
    @classmethod
    def read_from(cls, data_stream, num_to_read):
        evlr_list = cls()
        for _ in range(num_to_read):
            raw = RawEVLR.read_from(data_stream)
            try:
                evlr_list.append(evlr_factory(raw))
            except UnicodeDecodeError:
                logger.error("Failed to decode VLR: {}".format(raw))

        return evlr_list
