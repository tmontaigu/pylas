import io
import struct

from . import vlr, evlr
from pylas.point import record, dims
from .compression import (is_point_format_compressed,
                          compressed_id_to_uncompressed)
from .headers import rawheader
from .lasdatas import las12, las14, base

USE_UNPACKED = False


def open_las(source):
    if isinstance(source, bytes):
        return read_las_buffer(source)
    elif isinstance(source, str):
        return read_las_file(source)
    else:
        return read_las_stream(source)


def read_las_file(filename):
    with open(filename, mode='rb') as fin:
        return read_las_stream(fin)


def read_las_buffer(buffer):
    with io.BytesIO(buffer) as stream:
        return read_las_stream(stream)


def read_las_stream(data_stream):
    point_record = record.UnpackedPointRecord if USE_UNPACKED else record.PackedPointRecord

    header = rawheader.RawHeader.read_from(data_stream)
    assert data_stream.tell() == header.header_size
    vlrs = vlr.VLRList.read_from(data_stream, num_to_read=header.number_of_vlr)

    extra_bytes_vlr = vlrs.get_extra_bytes_vlr()
    if extra_bytes_vlr is not None:
        extra_dims = extra_bytes_vlr.type_of_extra_dims()
    else:
        extra_dims = None

    data_stream.seek(header.offset_to_point_data)
    if is_point_format_compressed(header.point_data_format_id):
        laszip_vlr = vlrs.extract_laszip_vlr()
        if laszip_vlr is None:
            raise ValueError('Could not find Laszip VLR')
        header.point_data_format_id = compressed_id_to_uncompressed(
            header.point_data_format_id)

        offset_to_chunk_table = struct.unpack('<q', data_stream.read(8))[0]
        size_of_point_data = offset_to_chunk_table - data_stream.tell()
        points = point_record.from_compressed_buffer(
            data_stream.read(size_of_point_data),
            header.point_data_format_id,
            header.number_of_point_records,
            laszip_vlr
        )
    else:
        points = point_record.from_stream(
            data_stream,
            header.point_data_format_id,
            header.number_of_point_records,
            extra_dims
        )


    # TODO las 1.3 should maybe, have its own class
    if header.version_major >= 1 and header.version_minor >= 3:
        evlrs = [evlr.RawEVLR.read_from(data_stream) for _ in range(header.number_of_evlr)]
        return las14.LasData(header=header, vlrs=vlrs, points=points, evlrs=evlrs)

    return las12.LasData(header=header, vlrs=vlrs, points=points)


def convert(source, destination=None, *, point_format_id=None):
    source_las = open_las(source) if not isinstance(source, base.LasBase) else source

    if point_format_id is None:
        return

    file_version = dims.min_file_version_for_point_format(point_format_id)

    header = source_las.header
    header.version_major = int(file_version[0])
    header.version_minor = int(file_version[2])
    header.point_data_format_id = point_format_id
    header.header_size = rawheader.LAS_HEADERS_SIZE[file_version]

    source_las.points_data.to_point_format(point_format_id)
    points = source_las.points_data

    try:
        evlrs = source_las.evlrs
    except ValueError:
        evlrs = []

    if file_version >= '1.4':
        out_las = las14.LasData(header=header, vlrs=source_las.vlrs, points=points, evlrs=evlrs)
    else:
        out_las = las12.LasData(header=header, vlrs=source_las.vlrs, points=points)

    if destination is not None:
        out_las.write(destination)
    else:
        return out_las


def create_las(point_format=0, file_version=None):
    if file_version is not None and point_format not in dims.VERSION_TO_POINT_FMT[file_version]:
        raise ValueError('Point format {} is not compatible with file version {}'.format(
            point_format, file_version
        ))
    else:
        file_version = dims.min_file_version_for_point_format(point_format)

    header = rawheader.RawHeader()
    header.version_major = int(file_version[0])
    header.version_minor = int(file_version[2])
    header.point_data_format_id = point_format
    header.header_size = rawheader.LAS_HEADERS_SIZE[file_version]

    if file_version >= '1.4':
        return las14.LasData(header=header)
    return las12.LasData(header=header)
