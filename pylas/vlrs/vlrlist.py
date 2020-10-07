import logging
from typing import BinaryIO, Type, List

from .known import vlr_factory, IKnownVLR
from .rawvlr import RawVLR

logger = logging.getLogger(__name__)


class RawVLRList:
    """A RawVLRList is like a VLR list but it should only
    hold RawVLRs.

    This class is meant to make it easier to write VLRS the the file and know in advance
    the size in bytes taken by all the VLRs combined

    """

    def __init__(self, iterable=None):
        if iterable is not None:
            self.vlrs = list(iterable)
        else:
            self.vlrs = []

    def append(self, raw_vlr):
        self.vlrs.append(raw_vlr)

    def __len__(self):
        return len(self.vlrs)

    def total_size_in_bytes(self):
        return sum(v.size_in_bytes() for v in self.vlrs)

    def write_to(self, out_stream):
        """Writes all the raw vlrs contained in list to
        the out_stream

        Parameters
        ----------
        out_stream: io.RawIOBase
            The stream where vlrs will be written to

        """
        for vlr in self.vlrs:
            vlr.write_to(out_stream)

    def __iter__(self):
        return iter(self.vlrs)

    @classmethod
    def from_list(cls, vlrs):
        """Construct a RawVLR list from a list of vlrs

        Parameters
        ----------
        vlrs: iterable of VLR

        Returns
        -------
        RawVLRList

        """
        raw_vlrs = cls()
        for vlr in vlrs:
            raw = RawVLR()
            raw.header.user_id = vlr.user_id.encode("utf8")
            raw.header.description = vlr.description.encode("utf8")
            raw.header.record_id = vlr.record_id
            raw.record_data = vlr.record_data_bytes()
            raw_vlrs.append(raw)
        return raw_vlrs


class VLRList:
    """Class responsible for managing the vlrs"""

    def __init__(self):
        self.vlrs = []

    def append(self, vlr):
        """append a vlr to the list

        Parameters
        ----------
        vlr: RawVlR or VLR or KnownVlr

        Returns
        -------

        """
        self.vlrs.append(vlr)

    def extend(self, vlr_list):
        """append all elements of the vlr_list into self"""
        self.vlrs.extend(vlr_list)

    def get_by_id(self, user_id="", record_ids=(None,)):
        """Function to get vlrs by user_id and/or record_ids.
        Always returns a list even if only one vlr matches the user_id and record_id

        >>> import pylas
        >>> from pylas.vlrs.known import ExtraBytesVlr, WktCoordinateSystemVlr
        >>> las = pylas.read("pylastests/extrabytes.las")
        >>> las.vlrs
        [<ExtraBytesVlr(extra bytes structs: 5)>]
        >>> las.vlrs.get(WktCoordinateSystemVlr.official_user_id())
        []
        >>> las.vlrs.get(WktCoordinateSystemVlr.official_user_id())[0]
        Traceback (most recent call last):
        IndexError: list index out of range
        >>> las.vlrs.get_by_id(ExtraBytesVlr.official_user_id())
        [<ExtraBytesVlr(extra bytes structs: 5)>]
        >>> las.vlrs.get_by_id(ExtraBytesVlr.official_user_id())[0]
        <ExtraBytesVlr(extra bytes structs: 5)>

        Parameters
        ----------
        user_id: str, optional
                 the user id
        record_ids: iterable of int, optional
                    THe record ids of the vlr(s) you wish to get

        Returns
        -------
        :py:class:`list`
            a list of vlrs matching the user_id and records_ids

        """
        if user_id != "" and record_ids != (None,):
            return [
                vlr
                for vlr in self.vlrs
                if vlr.user_id == user_id and vlr.record_id in record_ids
            ]
        else:
            return [
                vlr
                for vlr in self.vlrs
                if vlr.user_id == user_id or vlr.record_id in record_ids
            ]

    def get(self, vlr_type):
        """Returns the list of vlrs of the requested type
        Always returns a list even if there is only one VLR of type vlr_type.

        >>> import pylas
        >>> las = pylas.read("pylastests/extrabytes.las")
        >>> las.vlrs
        [<ExtraBytesVlr(extra bytes structs: 5)>]
        >>> las.vlrs.get("WktCoordinateSystemVlr")
        []
        >>> las.vlrs.get("WktCoordinateSystemVlr")[0]
        Traceback (most recent call last):
        IndexError: list index out of range
        >>> las.vlrs.get('ExtraBytesVlr')
        [<ExtraBytesVlr(extra bytes structs: 5)>]
        >>> las.vlrs.get('ExtraBytesVlr')[0]
        <ExtraBytesVlr(extra bytes structs: 5)>


        Parameters
        ----------
        vlr_type: str
                  the class name of the vlr

        Returns
        -------
        :py:class:`list`
            a List of vlrs matching the user_id and records_ids

        """
        return [v for v in self.vlrs if v.__class__.__name__ == vlr_type]

    def extract(self, vlr_type: Type[IKnownVLR]) -> List[IKnownVLR]:
        """Returns the list of vlrs of the requested type
        The difference with get is that the returned vlrs will be removed from the list

        Parameters
        ----------
        vlr_type: str
                  the class name of the vlr

        Returns
        -------
        list
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
        raise ValueError("{} is not in the VLR list".format(vlr_type))

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
    def read_from(cls, data_stream: BinaryIO, num_to_read: int) -> 'VLRList':
        """Reads vlrs and parse them if possible from the stream

        Parameters
        ----------
        data_stream : io.BytesIO
                      stream to read from
        num_to_read : int
                      number of vlrs to be read

        Returns
        -------
        pylas.vlrs.vlrlist.VLRList
            List of vlrs

        """
        vlrlist = cls()
        for _ in range(num_to_read):
            raw = RawVLR.read_from(data_stream)
            vlrlist.append(vlr_factory(raw))

        return vlrlist

    @classmethod
    def from_list(cls, vlr_list):
        vlrs = cls()
        vlrs.vlrs = vlr_list
        return vlrs
