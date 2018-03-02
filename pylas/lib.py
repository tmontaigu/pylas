import io
import struct

from . import pointdata, vlr
from .compression import (is_point_format_compressed,
                          compressed_id_to_uncompressed)
from .header import rawheader
from .lasdatas import las12, las14

USE_UNPACKED = True


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
    point_record = pointdata.UnpackedPointRecord if USE_UNPACKED else pointdata.PackedPointRecord

    header = rawheader.RawHeader.read_from(data_stream)
    assert data_stream.tell() == header.header_size
    vlrs = vlr.VLRList.read_from(data_stream, num_to_read=header.number_of_vlr)

    extra_bytes_vlr = vlrs.get_extra_bytes_vlr()
    if extra_bytes_vlr is not None:
        extra_dims = extra_bytes_vlr.type_of_extra_dims()
    else:
        extra_dims = None

    # version >= 1.3 -> EVLRs

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

    if header.version_major >= 1 and header.version_minor >= 4:
        return las14.LasData(header=header, vlrs=vlrs, points=points)

    return las12.LasData(header=header, vlrs=vlrs, points=points)


def convert(source, destination, *, point_format_id=None):
    source_las = open_las(source)

    if point_format_id is None:
        return

    source_las.points_data.to_point_format(point_format_id)
    source_las.write(destination)


# TODO creation with existing header, vlrs, evlrs, points
def create_las(file_version='1.2', point_format=0):
    # TODO check file version & point format compatibilty

    # For now we ca only create 1.2 files until
    # we have a proper way to create headers
    if not file_version == '1.2':
        raise NotImplementedError('Can only create 1.2 files for the moments')

    header = rawheader.RawHeader()
    header.point_data_format_id = point_format
    return las12.LasData(header=header)
