import ctypes

from .. import utils

NULL_BYTE = b"\x00"


class RawVLRHeader(ctypes.LittleEndianStructure):
    """Close representation of a VLR Header as it is written
    in the LAS file.
    """

    _pack_ = 1
    _fields_ = [
        ("_reserved", ctypes.c_uint16),
        ("user_id", ctypes.c_char * 16),
        ("record_id", ctypes.c_uint16),
        ("record_length_after_header", ctypes.c_uint16),
        ("description", ctypes.c_char * 32),
    ]

    @classmethod
    def from_stream(cls, stream):
        return cls.from_buffer(bytearray(stream.read(ctypes.sizeof(cls))))


VLR_HEADER_SIZE = ctypes.sizeof(RawVLRHeader)
MAX_VLR_RECORD_DATA_LEN = utils.ctypes_max_limit(
    RawVLRHeader.record_length_after_header.size
)


class RawVLR:
    """As close as possible to the underlying data
    No parsing of the record_data is made,
    every piece of data are still bytes.
    """

    def __init__(self):
        self.header = RawVLRHeader()
        self.record_data = b""

    @property
    def record_data(self):
        return self._record_data

    @record_data.setter
    def record_data(self, value):
        if len(value) > MAX_VLR_RECORD_DATA_LEN:
            raise OverflowError(
                "VLR record data length ({}) exceeds maximum ({})".format(
                    len(value), MAX_VLR_RECORD_DATA_LEN
                )
            )
        self.header.record_length_after_header = len(value)
        self._record_data = value

    def size_in_bytes(self):
        return VLR_HEADER_SIZE + self.header.record_length_after_header

    def write_to(self, out):
        """Write the raw header content to the out stream

        Parameters:
        ----------
        out : {file object}
            The output stream
        """

        out.write(bytes(self.header))
        out.write(self.record_data)

    @classmethod
    def read_from(cls, data_stream):
        """Instantiate a RawVLR by reading the content from the
        data stream

        Parameters:
        ----------
        data_stream : {file object}
            The input stream
        Returns
        -------
        RawVLR
            The RawVLR read
        """

        raw_vlr = cls()
        header = RawVLRHeader.from_stream(data_stream)
        raw_vlr.header = header
        raw_vlr.record_data = data_stream.read(header.record_length_after_header)
        return raw_vlr

    def __repr__(self):
        return "<RawVLR(user_id: {}, record_id: {}, len: {})>".format(
            self.header.user_id,
            self.header.record_id,
            self.header.record_length_after_header,
        )


class BaseVLR:
    def __init__(self, user_id, record_id, description=""):
        self.user_id = user_id
        self.record_id = record_id
        self.description = description


class VLR(BaseVLR):
    def __init__(self, user_id, record_id, description=""):
        super().__init__(user_id, record_id, description=description)
        self.record_data = b""

    def record_data_bytes(self):
        return self.record_data

    @classmethod
    def from_raw(cls, raw_vlr):
        vlr = cls(
            raw_vlr.header.user_id.rstrip(NULL_BYTE).decode(),
            raw_vlr.header.record_id,
            raw_vlr.header.description.rstrip(NULL_BYTE).decode(),
        )
        vlr.record_data = raw_vlr.record_data
        return vlr

    def __eq__(self, other):
        return (
            self.record_id == other.record_id
            and self.user_id == other.user_id
            and self.description == other.description
            and self.record_data == other.record_data
        )

    def __repr__(self):
        return "<{}(user_id: '{}', record_id: '{}', data len: {})>".format(
            self.__class__.__name__, self.user_id, self.record_id, len(self.record_data)
        )
