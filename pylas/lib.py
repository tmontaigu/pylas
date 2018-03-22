""" 'Entry point' of the library,
 Contains the various functions meant to be use directly by a user
"""
import io
import logging
import struct

import pylas.vlrs.rawvlr
import pylas.vlrs.vlrlist
from . import errors
from . import evlr
from . import headers
from .compression import (compressed_id_to_uncompressed,
                          is_point_format_compressed,
                          laszip_decompress)
from .lasdatas import las12, las14
from .point import dims, record

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
    buffer : {bytes | bytearray}
        The buffer containing the LAS file
    Returns
    -------
    LasData
    """
    with io.BytesIO(buffer) as stream:
        return read_las_stream(stream)


def read_las_stream(data_stream):
    """ Reads a stream (file object like)

    Parameters:
    ----------
    data_stream : {file object}

    Returns
    -------
    LasData
    """
    stream_start_pos = data_stream.tell()
    header = headers.HeaderFactory().read_from_stream(data_stream)

    offset_diff = header.header_size - data_stream.tell()
    if offset_diff != 0:
        _warn_diff_not_zero(offset_diff, 'end of Header', 'start of VLRs')
        data_stream.seek(header.header_size)

    vlrs = pylas.vlrs.vlrlist.VLRList.read_from(data_stream, num_to_read=header.number_of_vlr)

    try:
        extra_dims = vlrs.get('ExtraBytesVlr')[0].type_of_extra_dims()
    except IndexError:
        extra_dims = None

    offset_diff = header.offset_to_point_data - data_stream.tell()
    if offset_diff != 0:
        _warn_diff_not_zero(offset_diff, 'end of VLRs', 'start of point records')
        data_stream.seek(header.offset_to_point_data)

    if is_point_format_compressed(header.point_data_format_id):
        laszip_vlr = vlrs.pop(vlrs.index('LasZipVlr'))
        header.point_data_format_id = compressed_id_to_uncompressed(
            header.point_data_format_id)

        try:
            points = _read_compressed_points_data(
                data_stream,
                header.point_data_format_id,
                header.number_of_point_records,
                laszip_vlr
            )
        except (RuntimeError, errors.LazPerfNotFound) as e:
            logging.error("LazPerf failed to decompress ({}), trying laszip.".format(e))
            data_stream.seek(stream_start_pos)
            return read_las_buffer(laszip_decompress(data_stream))

    else:
        points = record.PackedPointRecord.from_stream(
            data_stream,
            header.point_data_format_id,
            header.number_of_point_records,
            extra_dims
        )

        if dims.format_has_waveform_packet(header.point_data_format_id):
            is_internal, is_external = header.global_encoding.waveform_internal, header.global_encoding.waveform_external
            if is_internal == is_external:
                raise ValueError(
                    'Incoherent values for internal and external waveform flags, both are {})'.format(
                        'set' if is_internal else 'unset'
                    ))

            if is_internal:
                # TODO: Find out what to do with these
                _, _ = _read_internal_waveform_packet(data_stream, header)
            elif is_external:
                logging.info(
                    "Waveform data is in an external file, you'll have to load it yourself")

    if header.version_major >= 1 and header.version_minor >= 4:
        evlrs = [evlr.RawEVLR.read_from(data_stream)
                 for _ in range(header.number_of_evlr)]
        return las14.LasData(header=header, vlrs=vlrs, points=points, evlrs=evlrs)

    return las12.LasData(header=header, vlrs=vlrs, points=points)


def _warn_diff_not_zero(diff, end_of, start_of):
    logging.warning("There are {} bytes between {} and {}".format(diff, end_of, start_of))


def _read_compressed_points_data(data_stream, point_format_id, num_points, laszip_vlr):
    offset_to_chunk_table = struct.unpack('<q', data_stream.read(8))[0]
    size_of_point_data = offset_to_chunk_table - data_stream.tell()

    if offset_to_chunk_table <= 0:
        logging.warning("Strange offset to chunk table: {}, ignoring it..".format(
            offset_to_chunk_table))
        size_of_point_data = -1  # Read everything

    points = record.PackedPointRecord.from_compressed_buffer(
        data_stream.read(size_of_point_data),
        point_format_id,
        num_points,
        laszip_vlr
    )
    return points


def _read_internal_waveform_packet(data_stream, header):
    offset_diff = data_stream.tell() - header.start_of_waveform_data_packet_record
    if offset_diff != 0:
        _warn_diff_not_zero(offset_diff, 'end of point records', 'start of waveform data')
        data_stream.seek(-offset_diff, io.SEEK_CUR)
    # This is strange, the spec says, waveform data packet is in a EVLR
    #  but in the 2 samples I have its a VLR
    # but also the 2 samples have a wrong user_id (LAS_Spec instead of LASF_Spec)
    b = bytearray(data_stream.read(pylas.vlrs.rawvlr.VLR_HEADER_SIZE))
    waveform_header = pylas.vlrs.rawvlr.VLRHeader.from_buffer(b)
    waveform_record = data_stream.read()
    logging.info(waveform_header.user_id, waveform_header.record_id,
                 waveform_header.record_length_after_header)
    logging.debug("Read: {} MBytes of waveform_record".format(
        len(waveform_record) / 10 ** 6))

    return waveform_header, waveform_record


def convert(source_las, *, point_format_id=None, file_version=None):
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

    if file_version is None:
        file_version = dims.min_file_version_for_point_format(point_format_id)
        # Don't downgrade the file version
        if file_version < source_las.header.version:
            file_version = source_las.header.version
    elif dims.is_point_fmt_compatible_with_version(point_format_id, file_version):
        file_version = str(file_version)
    else:
        raise ValueError('Point format {} is not compatible with file version {}'.format(
            point_format_id, file_version))

    header = source_las.header
    header.version = file_version
    header.point_data_format_id = point_format_id

    points = record.PackedPointRecord.from_point_record(
        source_las.points_data, point_format_id)

    try:
        evlrs = source_las.evlrs
    except ValueError:
        evlrs = []

    if file_version >= '1.4':
        return las14.LasData(header=header, vlrs=source_las.vlrs, points=points, evlrs=evlrs)
    return las12.LasData(header=header, vlrs=source_las.vlrs, points=points)


def create_from_header(header):
    if header.version >= '1.4':
        return las14.LasData(header=header)
    return las12.LasData(header=header)


def create_las(point_format=0, file_version=None):
    if file_version is not None and point_format not in dims.VERSION_TO_POINT_FMT[file_version]:
        raise ValueError('Point format {} is not compatible with file version {}'.format(
            point_format, file_version
        ))
    else:
        file_version = dims.min_file_version_for_point_format(point_format)

    header = headers.HeaderFactory().new(file_version)
    header.point_data_format_id = point_format

    if file_version >= '1.4':
        return las14.LasData(header=header)
    return las12.LasData(header=header)
