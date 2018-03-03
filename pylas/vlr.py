import ctypes
from abc import ABC, abstractmethod
from collections import namedtuple

from .extradims import get_type_for_extra_dim
from .lasio import BinaryReader, BinaryWriter, type_lengths

NULL_BYTE = b'\x00'

VLRField = namedtuple('VLRField', ('name', 'type', 'num'))
VLR_HEADER_FIELDS = (
    VLRField('_reserved', 'uint16', 1),
    VLRField('user_id', 'str', 16),
    VLRField('record_id', 'uint16', 1),
    VLRField('record_length_after_header', 'uint16', 1),
    VLRField('description', 'str', 32),
)
VLR_HEADER_SIZE = sum((type_lengths[field.type] * field.num) for field in VLR_HEADER_FIELDS)


class RawVLR:
    def __init__(self):
        self._reserved = 0
        self._user_id = 16 * NULL_BYTE
        self.record_id = None
        self.record_length_after_header = 0
        self._description = 32 * NULL_BYTE
        self.record_data = b''

    @property
    def user_id(self):
        return self._user_id

    @user_id.setter
    def user_id(self, value):
        self._user_id = value + (16 - len(value)) * NULL_BYTE

    @property
    def description(self):
        return self._description

    @description.setter
    def description(self, value):
        self._description = value + (32 - len(value)) * NULL_BYTE

    def write_to(self, out):
        out_stream = BinaryWriter(out)
        for field in VLR_HEADER_FIELDS:
            value = getattr(self, field.name)
            out_stream.write(value, field.type, num=field.num)
        out_stream.write_raw(self.record_data)

    def __repr__(self):
        return 'RawVLR(user_id: {}, record_id: {}, len: {})'.format(
            self._user_id, self.record_id, self.record_length_after_header
        )

    @classmethod
    def read_from(cls, data_stream):
        bin_reader = BinaryReader(data_stream)
        raw_vlr = cls()
        for field in VLR_HEADER_FIELDS:
            value = bin_reader.read(field.type, num=field.num)
            setattr(raw_vlr, field.name, value)

        # TODO: Warn if empty payload ?
        raw_vlr.record_data = bin_reader.read('str', num=raw_vlr.record_length_after_header)
        return raw_vlr


class VLR:
    def __init__(self, user_id, record_id, description, data):
        self.user_id = user_id
        self.record_id = record_id
        self.description = description

        self.record_data = bytes(data)
        if len(self.record_data) < 0:
            raise ValueError('record length must be >= 0')

    def into_raw(self):
        raw_vlr = RawVLR()
        raw_vlr.user_id = self.user_id.encode('utf8')
        raw_vlr.description = self.description.encode('utf8')
        raw_vlr.record_id = self.record_id
        raw_vlr.record_length_after_header = len(self.record_data)
        raw_vlr.record_data = self.record_data

        return raw_vlr

    @classmethod
    def from_raw(cls, raw_vlr):
        vlr = cls(
            raw_vlr.user_id.rstrip(NULL_BYTE).decode(),
            raw_vlr.record_id,
            raw_vlr.description.rstrip(NULL_BYTE).decode(),
            raw_vlr.record_data
        )
        return vlr

    def __len__(self):
        return VLR_HEADER_SIZE + len(self.record_data)

    def __repr__(self):
        return "VLR(user_id: '{}', record_id: '{}', data len: '{}')".format(
            self.user_id, self.record_id, len(self.record_data))


class KnownVLR(ABC):
    @staticmethod
    @abstractmethod
    def official_user_id(): pass

    @staticmethod
    @abstractmethod
    def official_record_id(): pass


class ClassificationLookup(ctypes.LittleEndianStructure):
    _fields_ = [
        ('class_number', ctypes.c_uint8),
        ('description', ctypes.c_char * 15)
    ]

    def __init__(self, class_number, description):
        if isinstance(description, str):
            super().__init__(class_number, description.encode())
        else:
            super().__init__(class_number, description)

    def raw_bytes(self):
        return bytes(self)

    def __repr__(self):
        return 'ClassificationLookup({} : {})'.format(self.class_number, self.description)


class ClassificationLookupVlr(VLR, KnownVLR):
    def __init__(self, data=b''):
        super().__init__(self.official_user_id(), self.official_record_id(), "", data)
        self.lookups = []

    def add_lookup(self, class_number, description):
        if len(self.lookups) < 256:
            self.lookups.append(ClassificationLookup(class_number, description))
        else:
            raise ValueError('Cannot add more lookups')

    # fixme spec says rec_len = 16 * 256
    # we are only going to check is len(data) % 16
    def parse_data(self):
        if len(self.record_data) % 16 != 0:
            raise ValueError("Length of ClassificationLookup VLR's record_data must be a multiple of 16")
        for i in range(len(self.record_data) // ctypes.sizeof(ClassificationLookup)):
            self.lookups.append(ClassificationLookup.from_buffer(self.record_data[16 * i: 16 * (i + 1)]))

    def into_raw(self):
        self.record_data = b''.join(lookup.raw_bytes() for lookup in self.lookups)
        return super().into_raw()

    def __len__(self):
        return VLR_HEADER_SIZE + len(self.lookups) * ctypes.sizeof(ClassificationLookup)

    @staticmethod
    def official_user_id():
        return "LASF_Spec"

    @staticmethod
    def official_record_id():
        return 0


class LasZipVlr(VLR, KnownVLR):
    def __init__(self, data):
        super().__init__(
            LasZipVlr.official_user_id(),
            LasZipVlr.official_record_id(),
            'http://laszip.org',
            data
        )

    @staticmethod
    def official_user_id():
        return 'laszip encoded'

    @staticmethod
    def official_record_id():
        return 22204

    @classmethod
    def from_raw(cls, raw_vlr):
        return cls(raw_vlr.record_data)


class ExtraBytes(ctypes.LittleEndianStructure):
    _fields_ = [
        ('reserved', ctypes.c_uint8 * 2),
        ('data_type', ctypes.c_uint8),
        ('options', ctypes.c_uint8),
        ('name', ctypes.c_char * 32),
        ('unused', ctypes.c_uint8 * 4),
        ('no_data', ctypes.c_ubyte * 3),
        ('min', ctypes.c_ubyte * 3),
        ('max', ctypes.c_ubyte * 3),
        ('scale', ctypes.c_double * 3),
        ('offset', ctypes.c_double * 3),
        ('description', ctypes.c_char * 32),
    ]

    def format_name(self):
        return self.name.rstrip(NULL_BYTE).decode().replace(' ', "_").replace('-', '_')

    def type_tuple(self):
        if self.data_type == 0:
            return self.format_name(), '{}u1'.format(self.options)
        return self.format_name(), get_type_for_extra_dim(self.data_type)


class ExtraBytesVlr(VLR, KnownVLR):
    def __init__(self, data):
        if (len(data) % 192) != 0:
            raise ValueError("Data length of ExtraBytes vlr must be a multiple of 192")
        super().__init__('LASF_Spec', 4, 'extra_bytes', data)
        self.extra_bytes_structs = []
        self.parse_data()

    def parse_data(self):
        num_extra_bytes_structs = len(self.record_data) // 192
        self.extra_bytes_structs = [None] * num_extra_bytes_structs
        for i in range(num_extra_bytes_structs):
            self.extra_bytes_structs[i] = ExtraBytes.from_buffer_copy(self.record_data[192 * i: 192 * (i + 1)])

    def type_of_extra_dims(self):
        return [extra_dim.type_tuple() for extra_dim in self.extra_bytes_structs]

    def __repr__(self):
        return 'ExtraBytesVlr(extra bytes structs: {})'.format(len(self.extra_bytes_structs))

    @staticmethod
    def official_user_id():
        return 'LASF_Spec'

    @staticmethod
    def official_record_id():
        return 4

    @classmethod
    def from_raw(cls, raw_vlr):
        return cls(raw_vlr.record_data)


# TODO in a better way
def vlr_factory(raw_vlr):
    user_id = raw_vlr.user_id.rstrip(NULL_BYTE).decode()
    for known_vlr in KnownVLR.__subclasses__():
        if known_vlr.official_user_id() == user_id and known_vlr.official_record_id() == raw_vlr.record_id:
            return known_vlr.from_raw(raw_vlr)
    else:
        return VLR.from_raw(raw_vlr)


class VLRList:
    def __init__(self):
        self.vlrs = []

    def append(self, vlr):
        self.vlrs.append(vlr)

    def get_extra_bytes_vlr(self):
        for vlr in self.vlrs:
            if isinstance(vlr, ExtraBytesVlr):
                return vlr
        else:
            return None

    def extract_laszip_vlr(self):
        laszip_vlr_idx = self._laszip_vlr_idx()
        if laszip_vlr_idx is not None:
            return self.vlrs.pop(laszip_vlr_idx)
        return None

    def write_to(self, out):
        for vlr in self.vlrs:
            vlr.into_raw().write_to(out)

    def total_size_in_bytes(self):
        return sum(len(vlr) for vlr in self.vlrs)

    def _laszip_vlr_idx(self):
        for i, vlr in enumerate(self.vlrs):
            if isinstance(vlr, LasZipVlr):
                return i
        else:
            return None

    def __iter__(self):
        yield from iter(self.vlrs)

    def __getitem__(self, item):
        return self.vlrs[item]

    def __len__(self):
        return len(self.vlrs)

    def __eq__(self, other):
        if isinstance(other, list):
            return self.vlrs == other

    def __repr__(self):
        return "[{}]".format(", ".join(repr(vlr) for vlr in self.vlrs))

    @classmethod
    def read_from(cls, data_stream, num_to_read):
        vlrlist = cls()
        for _ in range(num_to_read):
            raw = RawVLR.read_from(data_stream)
            try:
                vlrlist.append(vlr_factory(raw))
            except UnicodeDecodeError:
                print("Failed to decode VLR: {}".format(raw))

        return vlrlist

    @classmethod
    def from_list(cls, vlr_list):
        vlrs = cls()
        vlrs.vlrs = vlr_list
        return vlrs
