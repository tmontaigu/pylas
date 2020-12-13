import enum
import logging
import struct
from datetime import date, timedelta
from typing import NamedTuple, BinaryIO, Optional, Tuple, List
from uuid import UUID

import numpy as np

from . import extradims
from .compression import (
    compressed_id_to_uncompressed,
    is_point_format_compressed,
    uncompressed_id_to_compressed,
)
from .errors import PylasError, UnknownExtraType
from .point import dims
from .point.format import PointFormat, ExtraBytesParams
from .point.record import PointRecord
from .vlrs.known import ExtraBytesStruct, ExtraBytesVlr
from .vlrs.vlrlist import VLRList, RawVLRList

logger = logging.getLogger(__name__)

LAS_FILE_SIGNATURE = b"LASF"


class Version(NamedTuple):
    major: int
    minor: int

    @classmethod
    def from_str(cls, string: str) -> "Version":
        major, minor = tuple(map(int, string.split(".")))
        return cls(major, minor)

    def __eq__(self, other):
        if isinstance(other, str):
            return str(self) == other
        else:
            return other.major == self.major and other.minor == self.minor

    def __str__(self):
        return f"{self.major}.{self.minor}"


class GpsTimeType(enum.IntEnum):
    WEEK_TIME = 0
    STANDARD = 1


class GlobalEncoding:
    GPS_TIME_TYPE_MASK = 0b0000_0000_0000_0001
    WAVEFORM_INTERNAL_MASK = 0b0000_0000_0000_0010  # 1.3
    WAVEFORM_EXTERNAL_MASK = 0b0000_0000_0000_0100  # 1.3
    SYNTHETIC_RETURN_NUMBERS_MASK = 0b0000_0000_0000_1000  # 1.3
    WKT_MASK = 0b0000_0000_0001_0000  # 1.4

    def __init__(self, value=0):
        self.value = value

    @property
    def gps_time_type(self) -> GpsTimeType:
        return GpsTimeType(self.value & self.GPS_TIME_TYPE_MASK)

    @property
    def waveform_internal(self) -> bool:
        return bool(self.value & self.WAVEFORM_INTERNAL_MASK)

    @property
    def waveform_external(self) -> bool:
        return bool(self.value & self.WAVEFORM_EXTERNAL_MASK)

    @property
    def synthetic_return_numbers(self) -> bool:
        return bool(self.value & self.SYNTHETIC_RETURN_NUMBERS_MASK)

    @property
    def wkt(self) -> bool:
        return bool(self.value & self.WKT_MASK)

    @classmethod
    def read_from(cls, stream: BinaryIO) -> "GlobalEncoding":
        return cls(int.from_bytes(stream.read(2), byteorder="little", signed=False))

    def write_to(self, stream: BinaryIO) -> None:
        stream.write(self.value.to_bytes(2, byteorder="little", signed=False))


class LasHeader:
    """Contains the information from the header of as LAS file
    with 'implementation' field left out and 'users' field
    stored in more ergonomic classes.

    This header also contains the VLRs
    """

    DEFAULT_VERSION = Version(1, 2)
    DEFAULT_POINT_FORMAT = PointFormat(3)

    def __init__(
        self,
        *,
        version: Optional[Version] = None,
        point_format: Optional[PointFormat] = None,
    ) -> None:
        if version is None and point_format is None:
            version = LasHeader.DEFAULT_VERSION
            point_format = LasHeader.DEFAULT_POINT_FORMAT
        elif version is not None and point_format is None:
            point_format = PointFormat(dims.min_point_format_for_version(str(version)))
        elif version is None and point_format is not None:
            version = Version.from_str(
                dims.min_file_version_for_point_format(point_format.id)
            )
        dims.raise_if_version_not_compatible_with_fmt(point_format.id, str(version))

        self.file_source_id: int = 0
        self.global_encoding: GlobalEncoding = GlobalEncoding()
        self.uuid: UUID = UUID(bytes_le=b"\0" * 16)
        self._version: Version = version
        self.system_identifier: str = "OTHER"
        self.generating_software: str = "pylas"
        self._point_format: PointFormat = point_format
        self.creation_date: Optional[date] = date.today()
        self.point_count: int = 0
        self.scales: np.ndarray = np.array([0.01, 0.01, 0.01], dtype=np.float64)
        self.offsets: np.ndarray = np.zeros(3, dtype=np.float64)
        self.maxs: np.ndarray = np.zeros(3, dtype=np.float64)
        self.mins: np.ndarray = np.zeros(3, dtype=np.float64)

        self.number_of_points_by_return: np.ndarray = np.zeros(15, dtype=np.uint32)

        self.vlrs: VLRList = VLRList()

        # Extra bytes between end of header and first vlrs
        self.extra_header_bytes: bytes = b""
        # Extra bytes between end of vlr end first point
        self.extra_vlr_bytes: bytes = b""

        # Las >= 1.3
        self.start_of_waveform_data_packet_record: int = 0

        # Las >= 1.4
        self.start_of_first_evlr: int = 0
        self.number_of_evlrs: int = 0

        # Info we keep because its useful for us but not the user
        self.offset_to_point_data: int = 0
        self.are_points_compressed: bool = False

        self.sync_extra_bytes_vlr()

    @property
    def point_format(self) -> PointFormat:
        return self._point_format

    @point_format.setter
    def point_format(self, new_point_format: PointFormat) -> None:
        dims.raise_if_version_not_compatible_with_fmt(
            new_point_format.id, str(self.version)
        )
        self._point_format = new_point_format
        self.sync_extra_bytes_vlr()

    @property
    def version(self) -> Version:
        return self._version

    @version.setter
    def version(self, version: Version) -> None:
        dims.raise_if_version_not_compatible_with_fmt(
            self.point_format.id, str(version)
        )
        self._version = version

    # scale properties
    @property
    def x_scale(self) -> float:
        return self.scales[0]

    @x_scale.setter
    def x_scale(self, value: float) -> None:
        self.scales[0] = value

    @property
    def y_scale(self) -> float:
        return self.scales[1]

    @y_scale.setter
    def y_scale(self, value: float) -> None:
        self.scales[1] = value

    @property
    def z_scale(self) -> float:
        return self.scales[2]

    @z_scale.setter
    def z_scale(self, value: float) -> None:
        self.scales[2] = value

    # offset properties
    @property
    def x_offset(self) -> float:
        return self.offsets[0]

    @x_offset.setter
    def x_offset(self, value: float) -> None:
        self.offsets[0] = value

    @property
    def y_offset(self) -> float:
        return self.offsets[1]

    @y_offset.setter
    def y_offset(self, value: float) -> None:
        self.offsets[1] = value

    @property
    def z_offset(self) -> float:
        return self.offsets[2]

    @z_offset.setter
    def z_offset(self, value: float) -> None:
        self.offsets[2] = value

    # max properties
    @property
    def x_max(self) -> float:
        return self.maxs[0]

    @x_max.setter
    def x_max(self, value: float) -> None:
        self.maxs[0] = value

    @property
    def y_max(self) -> float:
        return self.maxs[1]

    @y_max.setter
    def y_max(self, value: float) -> None:
        self.maxs[1] = value

    @property
    def z_max(self) -> float:
        return self.maxs[2]

    @z_max.setter
    def z_max(self, value: float) -> None:
        self.maxs[2] = value

    # min properties
    @property
    def x_min(self) -> float:
        return self.mins[0]

    @x_min.setter
    def x_min(self, value: float) -> None:
        self.mins[0] = value

    @property
    def y_min(self) -> float:
        return self.mins[1]

    @y_min.setter
    def y_min(self, value: float) -> None:
        self.mins[1] = value

    @property
    def z_min(self) -> float:
        return self.mins[2]

    @z_min.setter
    def z_min(self, value: float) -> None:
        self.mins[2] = value

    def add_extra_dims(self, params: List[ExtraBytesParams]) -> None:
        for param in params:
            self.point_format.add_extra_dimension(param)
        self.sync_extra_bytes_vlr()

    def add_extra_dim(self, params: ExtraBytesParams):
        self.add_extra_dims([params])

    def set_version_and_point_format(
        self, version: Version, point_format: PointFormat
    ) -> None:
        dims.raise_if_version_not_compatible_with_fmt(point_format.id, str(version))
        self._version = version
        self.point_format = point_format

    def partial_reset(self) -> None:
        self.creation_date = date.today()
        self.point_count = 0

        self.maxs = np.zeros(3, dtype=np.float64)
        self.mins = np.zeros(3, dtype=np.float64)
        self.number_of_points_by_return = np.zeros(15, dtype=np.uint32)

        self.start_of_first_evlr = 0
        self.number_of_evlrs = 0

    def update(self, points: PointRecord) -> None:
        self.x_max = max(
            self.x_max,
            (points["X"].max() * self.x_scale) + self.x_offset,
        )
        self.y_max = max(
            self.y_max,
            (points["Y"].max() * self.y_scale) + self.y_offset,
        )
        self.z_max = max(
            self.z_max,
            (points["Z"].max() * self.z_scale) + self.z_offset,
        )
        self.x_min = min(
            self.x_min,
            (points["X"].min() * self.x_scale) + self.x_offset,
        )
        self.y_min = min(
            self.y_min,
            (points["Y"].min() * self.y_scale) + self.y_offset,
        )
        self.z_min = min(
            self.z_min,
            (points["Z"].min() * self.z_scale) + self.z_offset,
        )

        for return_number, count in zip(
            *np.unique(points.return_number, return_counts=True)
        ):
            if return_number == 0:
                continue
            if return_number > len(self.number_of_points_by_return):
                break  # np.unique sorts unique values
            self.number_of_points_by_return[return_number - 1] += count
        self.point_count += len(points)

    def set_compressed(self, state: bool) -> None:
        self.are_points_compressed = state

    @classmethod
    def read_from(cls, stream: BinaryIO, seekable=True) -> "LasHeader":
        little_endian = "little"
        header = cls()

        file_sig = stream.read(4)
        if file_sig != LAS_FILE_SIGNATURE:
            raise PylasError(f'Invalid file signature "{file_sig}"')

        header.file_source_id = int.from_bytes(
            stream.read(2), little_endian, signed=False
        )
        header.global_encoding = GlobalEncoding.read_from(stream)

        header.uuid = UUID(bytes_le=stream.read(16))
        header._version = Version(
            int.from_bytes(stream.read(1), little_endian, signed=False),
            int.from_bytes(stream.read(1), little_endian, signed=False),
        )

        header.system_identifier = stream.read(32).rstrip(b"\0").decode()
        header.generating_software = stream.read(32).rstrip(b"\0").decode()

        creation_year = int.from_bytes(stream.read(2), little_endian, signed=False)
        creation_day_of_year = int.from_bytes(
            stream.read(2), little_endian, signed=False
        )
        try:
            header.creation_date = date(creation_year, 1, 1) + timedelta(
                creation_day_of_year - 1
            )
        except ValueError:
            header.creation_date = None

        header_size = int.from_bytes(stream.read(2), little_endian, signed=False)
        header.offset_to_point_data = int.from_bytes(
            stream.read(4), little_endian, signed=False
        )
        number_of_vlrs = int.from_bytes(stream.read(4), little_endian, signed=False)

        point_format_id = int.from_bytes(stream.read(1), little_endian, signed=False)
        point_size = int.from_bytes(stream.read(2), little_endian, signed=False)

        header.point_count = int.from_bytes(stream.read(4), little_endian, signed=False)
        for i in range(5):
            header.number_of_points_by_return[i] = int.from_bytes(
                stream.read(4), little_endian, signed=False
            )

        for i in range(3):
            header.scales[i] = struct.unpack("<d", stream.read(8))[0]
        for i in range(3):
            header.offsets[i] = struct.unpack("<d", stream.read(8))[0]
        for i in range(3):
            header.maxs[i] = struct.unpack("<d", stream.read(8))[0]
            header.mins[i] = struct.unpack("<d", stream.read(8))[0]

        if header.version.minor >= 3:
            header.start_of_waveform_data_packet_record = int.from_bytes(
                stream.read(8), little_endian, signed=False
            )
        if header.version.minor >= 4:
            header.start_of_first_evlr = int.from_bytes(
                stream.read(8), little_endian, signed=False
            )
            header.number_of_evlrs = int.from_bytes(
                stream.read(4), little_endian, signed=False
            )
            header.point_count = int.from_bytes(
                stream.read(8), little_endian, signed=False
            )
            for i in range(15):
                header.number_of_points_by_return[i] = int.from_bytes(
                    stream.read(8), little_endian, signed=False
                )
        if seekable:
            current_pos = stream.tell()
            if current_pos < header_size:
                header.extra_header_bytes = stream.read(header_size - current_pos)
            elif current_pos > header_size:
                raise PylasError("Incoherent header size")

        header.vlrs = VLRList.read_from(stream, num_to_read=number_of_vlrs)

        if seekable:
            current_pos = stream.tell()
            if current_pos < header.offset_to_point_data:
                header.extra_vlr_bytes = stream.read(
                    header.offset_to_point_data - current_pos
                )
            elif current_pos > header.offset_to_point_data:
                raise PylasError("Incoherent offset to point data")

        header.are_points_compressed = is_point_format_compressed(point_format_id)
        point_format_id = compressed_id_to_uncompressed(point_format_id)
        point_format = PointFormat(point_format_id)
        try:
            extra_dims = header.vlrs.get("ExtraBytesVlr")[0].type_of_extra_dims()
        except IndexError:
            pass
        else:
            if point_size == point_format.size:
                logger.warning(
                    "There is an ExtraByteVlr but the header.point_size matches the "
                    "point size without extra bytes. The extra bytes vlr info will be ignored"
                )
                header.vlrs.extract("ExtraBytesVlr")
            else:
                for extra_dim_info in extra_dims:
                    point_format.add_extra_dimension(extra_dim_info)
        header._point_format = point_format

        if point_size != point_format.size:
            raise PylasError("Incoherent point size")

        return header

    def write_to(self, stream: BinaryIO) -> None:
        little_endian = "little"
        raw_vlrs = RawVLRList.from_list(self.vlrs)
        assert len(raw_vlrs) == len(self.vlrs)

        stream.write(LAS_FILE_SIGNATURE)
        stream.write(self.file_source_id.to_bytes(2, little_endian, signed=False))
        self.global_encoding.write_to(stream)
        stream.write(self.uuid.bytes_le)
        stream.write(self.version.major.to_bytes(1, little_endian, signed=False))
        stream.write(self.version.minor.to_bytes(1, little_endian, signed=False))

        system_identifier = self.system_identifier.encode("ascii")
        if len(system_identifier) > 32:
            logger.warning(
                f"system identifier does not fit into the 32 maximum bytes,"
                f" it will be truncated"
            )
            stream.write(system_identifier[:32])
        else:
            stream.write(system_identifier.ljust(32, b"\0"))

        generating_software = self.generating_software.encode("ascii")
        if len(generating_software) > 32:
            logger.warning(
                f"generating software does not fit into the 32 maximum bytes,"
                f" it will be truncated"
            )
            stream.write(generating_software[:32])
        else:
            stream.write(generating_software.ljust(32, b"\0"))

        if self.creation_date is None:
            self.creation_date = date.today()

        stream.write(self.creation_date.year.to_bytes(2, little_endian, signed=False))
        stream.write(
            self.creation_date.timetuple().tm_yday.to_bytes(
                2, little_endian, signed=False
            )
        )

        header_size = LAS_HEADERS_SIZE[str(self.version)]
        self.offset_to_point_data = header_size + raw_vlrs.total_size_in_bytes()

        stream.write(header_size.to_bytes(2, little_endian, signed=False))
        stream.write(self.offset_to_point_data.to_bytes(4, little_endian, signed=False))
        stream.write(len(raw_vlrs).to_bytes(4, little_endian, signed=False))

        point_format_id = self.point_format.id
        if self.are_points_compressed:
            point_format_id = uncompressed_id_to_compressed(point_format_id)
        stream.write(point_format_id.to_bytes(1, little_endian, signed=False))
        stream.write(self.point_format.size.to_bytes(2, little_endian, signed=False))

        # Point Count
        if self.version.minor >= 4:
            stream.write(int(0).to_bytes(4, little_endian, signed=False))
            for i in range(5):
                stream.write(int(0).to_bytes(4, little_endian, signed=False))
        else:
            if self.point_count > np.iinfo(np.uint32).max:
                raise PylasError(
                    f"Version {self.version} cannot save clouds with more than"
                    f" {np.iinfo(np.uint32).max} points"
                )

            stream.write(self.point_count.to_bytes(4, little_endian, signed=False))
            for i in range(5):
                stream.write(
                    int(self.number_of_points_by_return[i]).to_bytes(
                        4, little_endian, signed=False
                    )
                )

        for i in range(3):
            stream.write(struct.pack("<d", self.scales[i]))
        for i in range(3):
            stream.write(struct.pack("<d", self.offsets[i]))
        for i in range(3):
            stream.write(struct.pack("<d", self.maxs[i]))
            stream.write(struct.pack("<d", self.mins[i]))

        if self.version.minor >= 3:
            stream.write(
                self.start_of_waveform_data_packet_record.to_bytes(
                    8, little_endian, signed=False
                )
            )

        if self.version.minor >= 4:
            stream.write(
                self.start_of_first_evlr.to_bytes(8, little_endian, signed=False)
            )
            stream.write(self.number_of_evlrs.to_bytes(4, little_endian, signed=False))
            stream.write(self.point_count.to_bytes(8, little_endian, signed=False))
            for i in range(15):
                stream.write(
                    int(self.number_of_points_by_return[i]).to_bytes(
                        8, little_endian, signed=False
                    )
                )

        raw_vlrs.write_to(stream)

    def sync_extra_bytes_vlr(self) -> None:
        try:
            self.vlrs.extract("ExtraBytesVlr")
        except IndexError:
            pass

        eb_vlr = ExtraBytesVlr()
        for extra_dimension in self.point_format.extra_dimensions:
            type_str = extra_dimension.type_str()
            assert type_str is not None

            eb_struct = ExtraBytesStruct(
                name=extra_dimension.name.encode(),
                description=extra_dimension.description.encode(),
            )

            if extra_dimension.num_elements > 3 and type_str[-2:] == "u1":
                type_id = 0
                eb_struct.options = extra_dimension.num_elements
            else:
                type_id = extradims.get_id_for_extra_dim_type(type_str)

            if extra_dimension.scales is not None:
                eb_struct.set_scale_is_relevant()
                for i in range(extra_dimension.num_elements):
                    eb_struct.scale[i] = extra_dimension.scales[i]

            if extra_dimension.offsets is not None:
                eb_struct.set_offset_is_relevant()
                for i in range(extra_dimension.num_elements):
                    eb_struct.offset[i] = extra_dimension.offsets[i]

            eb_struct.data_type = type_id
            eb_vlr.extra_bytes_structs.append(eb_struct)

        self.vlrs.append(eb_vlr)

    def __repr__(self) -> str:
        return f"<LasHeader({self.version.major}.{self.version.minor}, {self.point_format})>"


LAS_HEADERS_SIZE = {
    "1.2": 227,
    "1.3": 235,
    "1.4": 375,
}
