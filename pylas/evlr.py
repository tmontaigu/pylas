from collections import namedtuple

EVLR_HEADER_SIZE = 60
EvlrHeaderField = namedtuple("EvlrHeaderField", ('name', 'type', 'num'))

EVLR_HEADER_FIELDS = (
    EvlrHeaderField('reserved', 'uint16', 1),
    EvlrHeaderField('user_id', 'str', 16),
    EvlrHeaderField('record_id', 'uint16', 1),
    EvlrHeaderField('record_length_after_header', 'uint64', 1),
    EvlrHeaderField('description', 'str', 32),
)

class RawEVLR:
    def __init__(self):
        self.reserved = 0
        self.user_id = b'\x00' * 16
        self.record_id = 0
        self.record_length_after_header = 0
        self.description = b'\x00' * 32
        self.record_data = b''

class EVLR:
    def __init__(self):
        pass
