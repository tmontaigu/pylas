from .known import vlr_factory
from .rawvlr import RawVLR


class VLRList:
    """ Class responsible for managing the vlrs
    """
    def __init__(self):
        self.vlrs = []

    def append(self, vlr):
        """ append a vlr to the list

        Parameters
        ----------
        vlr: RawVlR | KnownVlr

        Returns
        -------

        """
        self.vlrs.append(vlr)

    def extend(self, vlr_list):
        """ append all elements of the vlr_list into self
        """
        self.vlrs.extend(vlr_list)

    def get_by_id(self, user_id='', record_ids=(None,)):
        """ Function to get vlrs by user_id and/or record_ids

        Parameters
        ----------
        user_id: str, optional
            the user id
        record_ids: Iterable if int, optional
            THe record ids of the vlr(s) you wish to get

        Returns
        -------
        a List of vlrs matching the user_id and records_ids

        """
        if user_id != '' and record_ids != (None,):
            return [vlr for vlr in self.vlrs if vlr.user_id == user_id and vlr.record_id in record_ids]
        else:
            return [vlr for vlr in self.vlrs if vlr.user_id == user_id or vlr.record_id in record_ids]

    def get(self, vlr_type):
        """ Returns the list of vlr of the requested ype

        Parameters
        ----------
        vlr_type: str, the class name of the vlr

        Returns
        -------
        a List of vlrs matching the user_id and records_ids

        """
        return [v for v in self.vlrs if v.__class__.__name__ == vlr_type]

    def extract(self, vlr_type):
        """ Returns the list of vlr of the requested ype
        The difference with get is that the returned vlrs will be removed from self

        Parameters
        ----------
        vlr_type: str, the class name of the vlr

        Returns
        -------
        a List of vlrs matching the user_id and records_ids

        """
        kept_vlrs, extracted_vlrs = [], []
        for vlr in self.vlrs:
            if vlr.__class__.__name__ == vlr_type:
                extracted_vlrs.append(vlr)
            else:
                kept_vlrs.append(vlr)
        self.vlrs = kept_vlrs
        return extracted_vlrs

    def pop(self, index):
        return self.vlrs.pop(index)

    def index(self, vlr_type):
        for i, v in enumerate(self.vlrs):
            if v.__class__.__name__ == vlr_type:
                return i
        else:
            raise ValueError('{} is not in the VLR list'.format(vlr_type))

    def write_to(self, out):
        for vlr in self.vlrs:
            vlr.into_raw().write_to(out)

    def total_size_in_bytes(self):
        return sum(map(len, self.vlrs))

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
