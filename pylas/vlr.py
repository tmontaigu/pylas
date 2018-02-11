from pylas.header import BinaryReader


class RawVLR:
    def __init__(self):
        self._reserved = None
        self.user_id = None
        self.record_id = None
        self.record_length_after_header = None
        self.description = None
        self.record_data = None

    def write_to(self, out):
        pass

    def __repr__(self):
        return 'RawVLR(user_id: {}, record_id: {}, len: {})'.format(
            self.user_id, self.record_id, self.record_length_after_header
        )

    @classmethod
    def read_from(cls, data_stream):
        bin_reader = BinaryReader(data_stream)
        raw_vlr = cls()
        raw_vlr._reserved = bin_reader.read('uint16')
        raw_vlr.user_id = bin_reader.read('str', num=16)
        raw_vlr.record_id = bin_reader.read('uint16')
        raw_vlr.record_length_after_header = bin_reader.read('uint16')
        raw_vlr.description = bin_reader.read('str', num=32)
        # TODO: Warn if empty payload ?
        raw_vlr.record_data = bin_reader.read('str', num=raw_vlr.record_length_after_header)
        return raw_vlr
