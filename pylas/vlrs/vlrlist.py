import logging
from typing import BinaryIO, List

import numpy as np

from .known import vlr_factory, IKnownVLR
from .vlr import VLR

logger = logging.getLogger(__name__)


def encode_to_len(string: str, wanted_len: int) -> bytes:
    encoded_str = string.encode()

    missing_bytes = wanted_len - len(encoded_str)
    if missing_bytes < 0:
        raise ValueError(f"encoded str does not fit in {wanted_len} bytes")

    return encoded_str + (b"\0" * missing_bytes)


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

    def extract(self, vlr_type: str) -> List[IKnownVLR]:
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

    def copy(self):
        vlrs = VLRList()
        vlrs.vlrs = self.vlrs.copy()
        return vlrs

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
    def read_from(
            cls, data_stream: BinaryIO, num_to_read: int, extended: bool = False
    ) -> "VLRList":
        """Reads vlrs and parse them if possible from the stream

        Parameters
        ----------
        data_stream : io.BytesIO
                      stream to read from
        num_to_read : int
                      number of vlrs to be read

        extended : bool
                      whether the vlrs are regular vlr or extended vlr

        Returns
        -------
        pylas.vlrs.vlrlist.VLRList
            List of vlrs

        """
        vlrlist = cls()
        for _ in range(num_to_read):
            data_stream.read(2)
            user_id = data_stream.read(16).decode().rstrip("\0")
            record_id = int.from_bytes(
                data_stream.read(2), byteorder="little", signed=False
            )
            if extended:
                record_data_len = int.from_bytes(
                    data_stream.read(8), byteorder="little", signed=False
                )
            else:
                record_data_len = int.from_bytes(
                    data_stream.read(2), byteorder="little", signed=False
                )
            description = data_stream.read(32).decode().rstrip("\0")
            record_data_bytes = data_stream.read(record_data_len)

            vlr = VLR(user_id, record_id, description, record_data_bytes)

            vlrlist.append(vlr_factory(vlr))

        return vlrlist

    def write_to(self, stream: BinaryIO, as_extended: bool = False) -> int:
        bytes_written = 0
        for vlr in self.vlrs:
            record_data = vlr.record_data_bytes()

            stream.write(b"\0\0")
            stream.write(encode_to_len(vlr.user_id, 16))
            stream.write(vlr.record_id.to_bytes(2, byteorder="little", signed=False))
            if as_extended:
                if len(record_data) > np.iinfo("uint16").max:
                    raise ValueError("vlr record_data is too long")
                stream.write(len(record_data).to_bytes(8, byteorder="little", signed=False))
            else:
                stream.write(len(record_data).to_bytes(2, byteorder="little", signed=False))
            stream.write(encode_to_len(vlr.description, 32))
            stream.write(record_data)

            bytes_written += 54 if not as_extended else 60
            bytes_written += len(record_data)

        return bytes_written

    @classmethod
    def from_list(cls, vlr_list):
        vlrs = cls()
        vlrs.vlrs = vlr_list
        return vlrs
