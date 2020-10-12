""" The definition of the VLR Header, VLR, the KnownVLRs
 are in this module.

 A KnownVLR is a VLR for which we know how to parse its record_data
"""
import abc
import ctypes
import logging
import struct

from .rawvlr import NULL_BYTE, BaseVLR, VLR
from .. import extradims
from ..extradims import (
    get_type_for_extra_dim,
    get_kind_of_extra_dim,
)
from ..point.dims import DimensionInfo, DimensionKind

abstractmethod = abc.abstractmethod

logger = logging.getLogger(__name__)


class IKnownVLR(abc.ABC):
    """Interface that any KnownVLR must implement.
    A KnownVLR is a VLR for which we know how to parse its record_data

    Implementing this interfaces allows to automatically call the
    right parser for the right VLR when reading them.
    """

    @staticmethod
    @abstractmethod
    def official_user_id():
        """Shall return the official user_id as described in the documentation"""
        pass

    @staticmethod
    @abstractmethod
    def official_record_ids():
        """Shall return the official record_id for the VLR

        .. note::

            Even if the VLR has one record_id, the return type must be a tuple

        Returns
        -------
        tuple of int
            The record_ids this VLR type can have
        """
        pass

    @abstractmethod
    def record_data_bytes(self):
        """Shall return the bytes corresponding to the record_data part of the VLR
        as they should be written in the file.

        Returns
        -------
        bytes
            The bytes of the vlr's record_data

        """
        pass

    @abstractmethod
    def parse_record_data(self, record_data):
        """Shall parse the given record_data into a user-friendlier structure

        Parameters
        ----------
        record_data: bytes
            The record_data bytes read from the file

        """
        pass


class BaseKnownVLR(BaseVLR, IKnownVLR):
    """Base Class to factorize common code between the different type of Known VLRs"""

    def __init__(self, record_id=None, description=""):
        super().__init__(
            self.official_user_id(),
            self.official_record_ids()[0] if record_id is None else record_id,
            description,
        )

    @classmethod
    def from_raw(cls, raw):
        vlr = cls()
        vlr.description = raw.header.description.decode("ascii")
        vlr.parse_record_data(raw.record_data)
        return vlr


class ClassificationLookupVlr(BaseKnownVLR):
    """This vlr maps class numbers to short descriptions / names

    >>> lookup = ClassificationLookupVlr()
    >>> lookup[0] = "never_classified"
    >>> lookup[2] = "ground"
    >>> lookup[0]
    'never_classified'
    """

    _lookup_struct = struct.Struct("<B15s")

    def __init__(self):
        super().__init__(description="Classification Lookup")
        self.lookups = {}

    def parse_record_data(self, record_data):
        for class_id, desc in struct.iter_unpack("<B15s", record_data):
            # index using desc[i:i+1], because desc[i] gives an int, and we want a byte
            description = b"".join(
                desc[i:i+1] for i in range(len(desc)) if desc[i:i+1].isalnum() or desc[i:i+1] == b' '
            ).decode()
            self.lookups[class_id] = description

    def record_data_bytes(self):
        def lookup_converter(lookup_dict):
            for class_id, description in lookup_dict.items():
                description_bytes = description.encode("ascii")
                if len(description_bytes) > 15:
                    raise ValueError(
                        "decription ({}) is to long ({} bytes), it must not exceed 15 bytes when encoded".format(
                            description, len(description_bytes)
                        )
                    )
                yield class_id, description_bytes

        return b"".join(
            self._lookup_struct.pack(class_id, desc)
            for class_id, desc in lookup_converter(self.lookups)
        )

    def __getitem__(self, class_id):
        return self.lookups[class_id]

    def __setitem__(self, class_id, description):
        if class_id not in range(256):
            raise ValueError("Class id {} is not in range [0, 255]".format(class_id))

        self.lookups[class_id] = description

    @staticmethod
    def official_user_id():
        return "LASF_Spec"

    @staticmethod
    def official_record_ids():
        return (0,)


class LasZipVlr(BaseKnownVLR):
    """Contains the information needed by laszip (or any other laz backend)
    to compress the point records.
    """

    def __init__(self, data):
        super().__init__(description="http://laszip.org")
        self.record_data = data

    def parse_record_data(self, record_data):
        # Only laz backends know how to parse this
        pass

    def record_data_bytes(self):
        return self.record_data

    @staticmethod
    def official_user_id():
        return "laszip encoded"

    @staticmethod
    def official_record_ids():
        return (22204,)

    @classmethod
    def from_raw(cls, raw_vlr):
        return cls(raw_vlr.record_data)


class ExtraBytesStruct(ctypes.LittleEndianStructure):
    _pack_ = 1
    _fields_ = [
        ("reserved", ctypes.c_uint8 * 2),
        ("data_type", ctypes.c_uint8),
        ("options", ctypes.c_uint8),
        ("name", ctypes.c_char * 32),
        ("unused", ctypes.c_uint8 * 4),
        ("_no_data", (ctypes.c_byte * 8) * 3),
        ("_min", (ctypes.c_byte * 8) * 3),
        ("_max", (ctypes.c_byte * 8) * 3),
        ("_scale", (ctypes.c_byte * 8) * 3),
        ("_offset", (ctypes.c_byte * 8) * 3),
        ("description", ctypes.c_char * 32),
    ]

    _uint64t_struct = struct.Struct("<Q")
    _int64t_struct = struct.Struct("<q")
    _double_struct = struct.Struct("<d")

    def _struct_parser_for_kind(self):
        signedness = get_kind_of_extra_dim(self.data_type)

        if signedness == DimensionKind.FloatingPoint:
            return self._double_struct
        elif signedness == DimensionKind.SignedInteger:
            return self._int64t_struct
        elif signedness == DimensionKind.UnsignedInteger:
            return self._uint64t_struct
        else:
            return None

    def _parse_special_property(self, name):
        strct = self._struct_parser_for_kind()
        return tuple(strct.unpack(d)[0] for d in getattr(self, name))

    @classmethod
    def from_dimension_info(cls, info: DimensionInfo) -> "ExtraBytesStruct":
        if info.is_standard:
            raise ValueError("ExtraBytesStruct cannot describe standard dims")

        if info.kind == DimensionKind.BitField:
            raise ValueError("ExtraBytesStruct cannot describe bit fields")

        type_str = info.type_str()
        assert type_str is not None
        if type_str.endswith("u1"):
            extra_byte = cls(
                data_type=0,
                name=info.name.encode(),
                description="".encode(),
                options=int(type_str[:-2]),
            )
        else:
            if info.num_elements > 3:
                raise ValueError("Only u1 data type supports more than 3 elements")
            type_id = extradims.get_id_for_extra_dim_type(type_str)
            extra_byte = cls(
                data_type=type_id,
                name=info.name.encode(),
                description="".encode(),
            )

        return extra_byte

    @property
    def no_data(self):
        return self._parse_special_property("_no_data")

    @property
    def min(self):
        return self._parse_special_property("_min")

    @property
    def max(self):
        return self._parse_special_property("_max")

    @property
    def offset(self):
        return self._parse_special_property("_offset")

    @property
    def scale(self):
        return self._parse_special_property("_scale")

    def format_name(self):
        return self.name.rstrip(NULL_BYTE).decode().replace(" ", "_").replace("-", "_")

    def type_tuple(self):
        if self.data_type == 0:
            return self.format_name(), "{}u1".format(self.options)
        return self.format_name(), get_type_for_extra_dim(self.data_type)

    @staticmethod
    def size():
        return ctypes.sizeof(ExtraBytesStruct)

    def __repr__(self):
        return "<ExtraBytesStruct({}, {}, {})>".format(
            *self.type_tuple(), self.description
        )


class ExtraBytesVlr(BaseKnownVLR):
    def __init__(self):
        super().__init__(description="Extra Bytes Record")
        self.extra_bytes_structs = []

    def parse_record_data(self, data):
        if (len(data) % ExtraBytesStruct.size()) != 0:
            raise ValueError(
                "Data length of ExtraBytes vlr must be a multiple of {}".format(
                    ExtraBytesStruct.size()
                )
            )
        num_extra_bytes_structs = len(data) // ExtraBytesStruct.size()
        self.extra_bytes_structs = [None] * num_extra_bytes_structs
        for i in range(num_extra_bytes_structs):
            self.extra_bytes_structs[i] = ExtraBytesStruct.from_buffer_copy(
                data[ExtraBytesStruct.size() * i : ExtraBytesStruct.size() * (i + 1)]
            )

    def record_data_bytes(self):
        return b"".join(
            bytes(extra_struct) for extra_struct in self.extra_bytes_structs
        )

    def type_of_extra_dims(self):
        return [extra_dim.type_tuple() for extra_dim in self.extra_bytes_structs]

    def __repr__(self):
        return "<ExtraBytesVlr(extra bytes structs: {})>".format(
            len(self.extra_bytes_structs)
        )

    @staticmethod
    def official_user_id():
        return "LASF_Spec"

    @staticmethod
    def official_record_ids():
        return (4,)


class WaveformPacketStruct(ctypes.LittleEndianStructure):
    _pack_ = 1
    _fields_ = [
        ("bits_per_sample", ctypes.c_ubyte),
        ("waveform_compression_type", ctypes.c_ubyte),
        ("number_of_samples", ctypes.c_uint32),
        ("temporal_sample_spacing", ctypes.c_uint32),
        ("digitizer_gain", ctypes.c_double),
        ("digitizer_offset", ctypes.c_double),
    ]

    @staticmethod
    def size():
        return ctypes.sizeof(WaveformPacketStruct)


class WaveformPacketVlr(BaseKnownVLR):
    def __init__(self, record_id, description=""):
        super().__init__(record_id=record_id, description=description)
        self.parsed_record = None

    def parse_record_data(self, record_data):
        self.parsed_record = WaveformPacketStruct.from_buffer_copy(record_data)

    def record_data_bytes(self):
        return bytes(self.parsed_record)

    @staticmethod
    def official_record_ids():
        return range(100, 356)

    @staticmethod
    def official_user_id():
        return "LASF_Spec"

    @classmethod
    def from_raw(cls, raw_vlr):
        vlr = cls(
            raw_vlr.header.record_id, description=raw_vlr.header.description.decode()
        )
        vlr.description = raw_vlr.header.description
        vlr.parse_record_data(raw_vlr.record_data)
        return vlr


class GeoKeyEntryStruct(ctypes.LittleEndianStructure):
    _pack_ = 1
    _fields_ = [
        ("id", ctypes.c_uint16),
        ("tiff_tag_location", ctypes.c_uint16),
        ("count", ctypes.c_uint16),
        ("value_offset", ctypes.c_uint16),
    ]

    @staticmethod
    def size():
        return ctypes.sizeof(GeoKeysHeaderStructs)

    def __repr__(self):
        return "<GeoKey(Id: {}, Location: {}, count: {}, offset: {})>".format(
            self.id, self.tiff_tag_location, self.count, self.value_offset
        )


class GeoKeysHeaderStructs(ctypes.LittleEndianStructure):
    _pack_ = 1
    _fields_ = [
        ("key_direction_version", ctypes.c_uint16),
        ("key_revision", ctypes.c_uint16),
        ("minor_revision", ctypes.c_uint16),
        ("number_of_keys", ctypes.c_uint16),
    ]

    def __init__(self):
        super().__init__(
            key_directory_version=1, key_revision=1, minor_revision=0, number_of_kets=0
        )

    @staticmethod
    def size():
        return ctypes.sizeof(GeoKeysHeaderStructs)

    def __repr__(self):
        return "<GeoKeysHeader(vers: {}, rev:{}, minor: {}, num_keys: {})>".format(
            self.key_direction_version,
            self.key_revision,
            self.minor_revision,
            self.number_of_keys,
        )


class GeoKeyDirectoryVlr(BaseKnownVLR):
    def __init__(self):
        super().__init__(description="GeoTIFF GeoKeyDirectoryTag")
        self.geo_keys_header = GeoKeysHeaderStructs()
        self.geo_keys = [GeoKeyEntryStruct()]

    def parse_record_data(self, record_data):
        record_data = bytearray(record_data)
        header_data = record_data[: ctypes.sizeof(GeoKeysHeaderStructs)]
        self.geo_keys_header = GeoKeysHeaderStructs.from_buffer(header_data)
        self.geo_keys = []
        keys_data = record_data[GeoKeysHeaderStructs.size() :]
        num_keys = (
            len(record_data[GeoKeysHeaderStructs.size() :]) // GeoKeyEntryStruct.size()
        )
        if num_keys != self.geo_keys_header.number_of_keys:
            # print("Mismatch num keys")
            self.geo_keys_header.number_of_keys = num_keys

        for i in range(self.geo_keys_header.number_of_keys):
            data = keys_data[
                (i * GeoKeyEntryStruct.size()) : (i + 1) * GeoKeyEntryStruct.size()
            ]
            self.geo_keys.append(GeoKeyEntryStruct.from_buffer(data))

    def record_data_bytes(self):
        b = bytes(self.geo_keys_header)
        b += b"".join(map(bytes, self.geo_keys))
        return b

    def __repr__(self):
        return "<{}({} geo_keys)>".format(self.__class__.__name__, len(self.geo_keys))

    @staticmethod
    def official_user_id():
        return "LASF_Projection"

    @staticmethod
    def official_record_ids():
        return (34735,)


class GeoDoubleParamsVlr(BaseKnownVLR):
    def __init__(self):
        super().__init__(description="GeoTIFF GeoDoubleParamsTag")
        self.doubles = []

    def parse_record_data(self, record_data):
        sizeof_double = ctypes.sizeof(ctypes.c_double)
        if len(record_data) % sizeof_double != 0:
            raise ValueError(
                "GeoDoubleParams record data length () is not a multiple of sizeof(double) ()".format(
                    len(record_data), sizeof_double
                )
            )
        record_data = bytearray(record_data)
        num_doubles = len(record_data) // sizeof_double
        for i in range(num_doubles):
            b = record_data[i * sizeof_double : (i + 1) * sizeof_double]
            self.doubles.append(ctypes.c_double.from_buffer(b))

    def record_data_bytes(self):
        return b"".join(map(bytes, self.doubles))

    def __repr__(self):
        return "<GeoDoubleParamsVlr({})>".format(self.doubles)

    @staticmethod
    def official_user_id():
        return "LASF_Projection"

    @staticmethod
    def official_record_ids():
        return (34736,)


class GeoAsciiParamsVlr(BaseKnownVLR):
    def __init__(self):
        super().__init__(description="GeoTIFF GeoAsciiParamsTag")
        self.strings = []

    def parse_record_data(self, record_data):
        self.strings = [s.decode("ascii") for s in record_data.split(NULL_BYTE)]

    def record_data_bytes(self):
        return NULL_BYTE.join(s.encode("ascii") for s in self.strings)

    def __repr__(self):
        return "<GeoAsciiParamsVlr({})>".format(self.strings)

    @staticmethod
    def official_user_id():
        return "LASF_Projection"

    @staticmethod
    def official_record_ids():
        return (34737,)


class WktMathTransformVlr(BaseKnownVLR):
    """
    From the Spec:
        Note that the math transform WKT record is added for completeness, and a coordinate system WKT
        may or may not require a math transform WKT record

    """

    def __init__(self):
        super().__init__(description="")
        self.string = ""

    def _encode_string(self):
        return self.string.encode("utf-8") + NULL_BYTE

    def parse_record_data(self, record_data):
        self.string = record_data.decode("utf-8")

    def record_data_bytes(self):
        return self._encode_string()

    @staticmethod
    def official_user_id():
        return "LASF_Projection"

    @staticmethod
    def official_record_ids():
        return (2112,)


class WktCoordinateSystemVlr(BaseKnownVLR):
    """Replaces Coordinates Reference System for new las files (point fmt >= 5)
    "LAS is not using the “ESRI WKT”
    """

    def __init__(self, wkt_string=""):
        super().__init__(description="OGC Transformation Record")
        self.string = wkt_string

    def _encode_string(self):
        return self.string.encode("utf-8") + NULL_BYTE

    def parse_record_data(self, record_data):
        self.string = record_data.decode("utf-8")

    def record_data_bytes(self):
        return self._encode_string()

    @staticmethod
    def official_user_id():
        return "LASF_Projection"

    @staticmethod
    def official_record_ids():
        return (2112,)


def vlr_factory(raw_vlr):
    """Given a raw_vlr tries to find its corresponding KnownVLR class
    that can parse its data.
    If no KnownVLR implementation is found, returns a VLR (record_data will still be bytes)
    """
    user_id = raw_vlr.header.user_id.rstrip(NULL_BYTE).decode()
    known_vlrs = BaseKnownVLR.__subclasses__()
    for known_vlr in known_vlrs:
        if (
            known_vlr.official_user_id() == user_id
            and raw_vlr.header.record_id in known_vlr.official_record_ids()
        ):
            try:
                return known_vlr.from_raw(raw_vlr)
            except Exception as err:
                logger.warning(f"Failed to parse {known_vlr}: {err}")
                return VLR.from_raw(raw_vlr)

    return VLR.from_raw(raw_vlr)
