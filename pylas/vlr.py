from collections import namedtuple

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
        self.record_length = len(self.record_data)
        if self.record_length < 0:
            raise ValueError('record length must be >= 0')

    def is_laszip_vlr(self):
        return self.user_id == 'laszip encoded' and self.record_id == 22204

    def into_raw(self):
        raw_vlr = RawVLR()
        raw_vlr.user_id = self.user_id.encode()
        raw_vlr.description = self.description.encode()
        raw_vlr.record_id = self.record_id
        raw_vlr.record_length_after_header = len(self.record_data)
        raw_vlr.record_data = self.record_data

        print(raw_vlr)
        return raw_vlr

    @classmethod
    def from_raw(cls, raw_vlr):
        print(raw_vlr)
        vlr = cls(
            raw_vlr.user_id.rstrip(NULL_BYTE).decode(),
            raw_vlr.record_id,
            raw_vlr.description.rstrip(NULL_BYTE).decode(),
            raw_vlr.record_data
        )
        return vlr

    def __len__(self):
        return VLR_HEADER_SIZE + self.record_length

    def __repr__(self):
        return "VLR(user_id: '{}', record_id: '{}', data len: '{}')".format(
            self.user_id, self.record_id, self.record_length)


class LasZipVlr(VLR):
    def __init__(self, data):
        super().__init__('laszip encoded', 22204, 'http://laszip.org', data)
        if self.record_length != LasZipVlr.data_len():
            # If in the future the laszip data len changes, then there will be things to change
            # in our code and lazperf
            raise ValueError('Expected length of laszip vlr data to be 52 bytes')

    @staticmethod
    def data_len():
        return 52

    @staticmethod
    def len():
        return VLR_HEADER_SIZE + LasZipVlr.data_len()


class VLRList:
    def __init__(self):
        self.vlrs = []

    def append(self, vlr):
        self.vlrs.append(vlr)

    def extract_laszip_vlr(self):
        for vlr in self.vlrs:
            if vlr.is_laszip_vlr():
                return vlr
        else:
            return None

    # todo add the compressed optional param to know if include laszip vlr
    def write_to(self, out):
        for vlr in self.vlrs:
            vlr.into_raw().write_to(out)

    def __iter__(self):
        yield from iter(self.vlrs)

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
            vlrlist.append(VLR.from_raw(raw))

        return vlrlist

    @classmethod
    def from_list(cls, vlr_list):
        vlrs = cls()
        vlrs.vlrs = vlr_list
        return vlrs
