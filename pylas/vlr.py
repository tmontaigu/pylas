from pylas.header import BinaryReader


class RawVLR:
    def __init__(self):
        self._reserved = None
        self.user_id = None
        self.record_id = None
        self.record_length_after_header = None
        self.description = None
        self.record_data = None


    @classmethod
    def read_from(cls, data_stream):
        bin_reader = BinaryReader(data_stream)
        raw_vlr = cls()
        raw_vlr._reserved = bin_reader.read('uint16')
        raw_vlr.user_id = bin_reader.read('str', num=16)
        raw_vlr.record_id = bin_reader.read('uint16')
        raw_vlr.record_length_after_header = bin_reader.read('uint16')
        raw_vlr.description = bin_reader.read('str', num=32)
        # TODO: what to to in this situation ?
        if raw_vlr.record_length_after_header > 0:
            raw_vlr.record_data = bin_reader.read('str', num=raw_vlr.record_length_after_header)
        return raw_vlr


