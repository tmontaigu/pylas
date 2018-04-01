import ctypes
from abc import ABC, abstractmethod, abstractclassmethod

NULL_BYTE = b'\x00'


class VLRHeader(ctypes.LittleEndianStructure):
    _fields_ = [
        ('_reserved', ctypes.c_uint16),
        ('user_id', ctypes.c_char * 16),
        ('record_id', ctypes.c_uint16),
        ('record_length_after_header', ctypes.c_uint16),
        ('description', ctypes.c_char * 32)
    ]

    @classmethod
    def from_stream(cls, stream):
        return cls.from_buffer(bytearray(stream.read(ctypes.sizeof(cls))))


VLR_HEADER_SIZE = ctypes.sizeof(VLRHeader)


class RawVLR:
    """ As close as possible to the underlying data
    No parsing of the record_data is made
    """

    def __init__(self):
        self.header = VLRHeader()
        self.record_data = b''

    def write_to(self, out):
        """ Write the raw header content to the out stream

        Parameters:
        ----------
        out : {file object}
            The output stream
        """

        self.header.record_length_after_header = len(self.record_data)
        out.write(bytes(self.header))
        out.write(self.record_data)

    @classmethod
    def read_from(cls, data_stream):
        """ Instantiate a RawVLR by reading the content from the
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
        header = VLRHeader.from_stream(data_stream)
        raw_vlr.header = header
        raw_vlr.record_data = data_stream.read(header.record_length_after_header)
        return raw_vlr

    def __repr__(self):
        return 'RawVLR(user_id: {}, record_id: {}, len: {})'.format(
            self.header.user_id, self.header.record_id, self.header.record_length_after_header
        )


class UnknownVLR(ABC):
    @abstractmethod
    def into_raw(self): pass

    @abstractclassmethod
    def from_raw(cls, raw): pass


class BaseVLR(UnknownVLR):
    def __init__(self, user_id, record_id, description=''):
        self.user_id = user_id
        self.record_id = record_id
        self.description = description

    def into_raw(self):
        raw_vlr = RawVLR()
        raw_vlr.header.user_id = self.user_id.encode('utf8')
        raw_vlr.header.description = self.description.encode('utf8')
        raw_vlr.header.record_id = self.record_id
        raw_vlr.record_length_after_header = 0
        raw_vlr.record_data = b''
        return raw_vlr

    def __len__(self):
        return VLR_HEADER_SIZE


class VLR(BaseVLR):
    def __init__(self, user_id, record_id, description=''):
        super().__init__(user_id, record_id, description=description)
        self.record_data = b''

    def into_raw(self):
        raw_vlr = super().into_raw()
        raw_vlr.header.record_length_after_header = len(self.record_data)
        raw_vlr.record_data = self.record_data
        return raw_vlr

    @classmethod
    def from_raw(cls, raw_vlr):
        vlr = cls(
            raw_vlr.header.user_id.rstrip(NULL_BYTE).decode(),
            raw_vlr.header.record_id,
            raw_vlr.header.description.rstrip(NULL_BYTE).decode(),
        )
        vlr.record_data = raw_vlr.record_data
        return vlr

    def __len__(self):
        return VLR_HEADER_SIZE + len(self.record_data)

    def __repr__(self):
        return "{}(user_id: '{}', record_id: '{}', data len: '{}')".format(
            self.__class__.__name__, self.user_id, self.record_id, len(self.record_data))
