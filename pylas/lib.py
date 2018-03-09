import io
import struct
import warnings

from . import vlr, evlr
from .point import record, dims
from .compression import (is_point_format_compressed,
                          compressed_id_to_uncompressed)
from .headers import rawheader
from .lasdatas import las12, las14, base

USE_UNPACKED = False


def open_las(source):
    """" Entry point for reading las data in pylas
    It takes care of forwarding the call to the right function depending on
    the objects type

    Parameters:
    ----------
    source : {str | file_object | bytes | bytearray}
        The source to read data from
    Returns
    -------
    LasData object
        The object you can interact with to get access to the LAS points & VLRs
    """
    if isinstance(source, bytes) or isinstance(source, bytearray):
        return read_las_buffer(source)
    elif isinstance(source, str):
        return read_las_file(source)
    else:
        return read_las_stream(source)


def read_las_file(filename):
    """ Opens a file on disk and reads it

    Parameters:
    ----------
    filename : {str}
        The path to the file to read
    Returns
    -------
    LasData
    """
    with open(filename, mode='rb') as fin:
        return read_las_stream(fin)


def read_las_buffer(buffer):
    """ Wraps a buffer in a file object to be able to read it

    Parameters:
    ----------
    buffer : {bytes | bytarray}
        The buffer containing the LAS file
    Returns
    -------
    LasData
    """
    with io.BytesIO(buffer) as stream:
        return read_las_stream(stream)


# TODO: Sould probably raise instead of asserting, or at least warn
def read_las_stream(data_stream):
    """ Reads a stream (file object like)

    Parameters:
    ----------
    data_stream : {file object}

    Returns
    -------
    LasData
    """
    point_record = record.UnpackedPointRecord if USE_UNPACKED else record.PackedPointRecord
    header = rawheader.RawHeader.read_from(data_stream)

    offset_diff = header.header_size - data_stream.tell()
    if offset_diff != 0:
        err_str = 'There are {} user defined bytes between end of Header and start of VLR'.format(offset_diff)
        warnings.warn(err_str)
        data_stream.seek(offset_diff, io.SEEK_CUR)

    vlrs = vlr.VLRList.read_from(data_stream, num_to_read=header.number_of_vlr)

    try:
        extra_dims = vlrs.get_extra_bytes_vlr().type_of_extra_dims()
    except AttributeError:
        extra_dims = None

    offset_diff = header.offset_to_point_data - data_stream.tell()
    if offset_diff != 0:
        err_str = 'There are {} user defined bytes between end of VLRs and start of point records'.format(offset_diff)
        warnings.warn(err_str)
        data_stream.seek(offset_diff, io.SEEK_CUR)

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
    if header.version_major >= 1 and header.version_minor >= 4:
        evlrs = [evlr.RawEVLR.read_from(data_stream) for _ in range(header.number_of_evlr)]
        return las14.LasData(header=header, vlrs=vlrs, points=points, evlrs=evlrs)

    return las12.LasData(header=header, vlrs=vlrs, points=points)


def convert(source_las, *, point_format_id=None):
    """ Converts a Las from one point format to another
    Automatically upgrades the file version if source file version is not compatible with
    the new point_format_id

    # convert to point format 0
    las = pylas.open('autzen.las')
    las = pylas.convert(las, point_format_id=0)

    # convert to point format 6
    las = pylas.open('Stormwind.las')
    las = pylas.convert(las, point_format_id=6)

    Parameters:
    ----------
    source : {LasData}
        The source data to be converted

    point_format_id : {int}, optional
        The new point format id (the default is None, which won't change the source format id)

    Returns
    -------
    LasData if a destination is provided, else returns None
    """
    point_format_id = source_las.points_data.point_format_id if point_format_id is None else point_format_id

    # Don't downgrade the file version
    file_version = dims.min_file_version_for_point_format(point_format_id)
    if file_version < source_las.header.version:
        file_version = source_las.header.version

    header = source_las.header
    header.version = file_version
    header.point_data_format_id = point_format_id

    source_las.points_data.to_point_format(point_format_id)
    points = source_las.points_data

    try:
        evlrs = source_las.evlrs
    except ValueError:
        evlrs = []

    if file_version >= '1.4':
        return las14.LasData(header=header, vlrs=source_las.vlrs, points=points, evlrs=evlrs)
    return las12.LasData(header=header, vlrs=source_las.vlrs, points=points)



def create_las(point_format=0, file_version=None):
    if file_version is not None and point_format not in dims.VERSION_TO_POINT_FMT[file_version]:
        raise ValueError('Point format {} is not compatible with file version {}'.format(
            point_format, file_version
        ))
    else:
        file_version = dims.min_file_version_for_point_format(point_format)

    header = rawheader.RawHeader()
    header.version = str(file_version)
    header.point_data_format_id = point_format

    if file_version >= '1.4':
        return las14.LasData(header=header)
    return las12.LasData(header=header)
