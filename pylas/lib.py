""" 'Entry point' of the library, Contains the various functions meant to be
use directly by a user
"""

from . import headers
from .lasdatas import las12, las14
from .lasreader import LasReader
from .point import dims, record

USE_UNPACKED = False


def open_las(source, closefd=True):
    if isinstance(source, str):
        stream = open(source, mode='rb')
        if not closefd:
            raise ValueError("Cannot use closefd with filename")
    else:
        stream = source
    return LasReader(stream, closefd=closefd)


def read_las(source, closefd=True):
    """ Entry point for reading las data in pylas
    It takes care of forwarding the call to the right function depending on
    the objects type

    Parameters
    ----------
    source : {str | file_object}
        The source to read data from

    Returns
    -------
    LasData object
        The object you can interact with to get access to the LAS points & VLRs
    """
    with open_las(source, closefd=closefd) as reader:
        return reader.read()


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

    Parameters
    ----------
    source_las : {LasData}
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
    points = record.PackedPointRecord.zeros(header.point_data_format_id, header.number_of_point_records)
    if header.version >= '1.4':
        return las14.LasData(header=header, points=points)
    return las12.LasData(header=header, points=points)


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
