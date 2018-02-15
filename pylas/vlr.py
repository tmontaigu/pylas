from .lasio import BinaryReader

NULL_BYTE = b'\x00'

class RawVLR:
    def __init__(self):
        self._reserved = 2 * NULL_BYTE
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
        pass

    def __repr__(self):
        return 'RawVLR(user_id: {}, record_id: {}, len: {})'.format(
            self._user_id, self.record_id, self.record_length_after_header
        )

    @classmethod
    def read_from(cls, data_stream):
        bin_reader = BinaryReader(data_stream)
        raw_vlr = cls()
        raw_vlr._reserved = bin_reader.read('uint16')
        raw_vlr._user_id = bin_reader.read('str', num=16)
        raw_vlr.record_id = bin_reader.read('uint16')
        raw_vlr.record_length_after_header = bin_reader.read('uint16')
        raw_vlr.description = bin_reader.read('str', num=32)
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

    def into_raw(self):
        raw_vlr = RawVLR()
        raw_vlr.user_id = self.user_id.encode()
        raw_vlr.description = self.description.encode()
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

    def __repr__(self):
        return "VLR(user_id: '{}', record_id: '{}', len: '{}'".format(
            self.user_id, self.record_id, self.record_length)
