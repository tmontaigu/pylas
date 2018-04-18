""" 'Entry point' of the library, Contains the various functions meant to be
used directly by a user
"""

from . import headers
from .lasdatas import las12, las14
from .lasmmap import LasMMAP
from .lasreader import LasReader
from .point import dims, record

USE_UNPACKED = False


def open_las(source, closefd=True):
    """ Opens and reads the header of the las content in the source

    .. code:: python

        f = open('pylastests/simple.las', mode='rb')
        with open(f, closefd=False) as flas:
            print(flas.header)
        f.closed == False

        f = open('pylastests/simple.las', mode='rb')
        with open(f) as flas:
            las = flas.read()
        f.closed == True

    Parameters
    ----------
    source : stream | str
        if source is a str it must be a filename
        a stream if a file object with the methods read, seek, tell
    closefd: Whether the stream/file object shall be closed, this only work
    when using open_las in a with statement. An exception is raised if
    closefd is specified and the source is a filename


    Returns
    -------
    pylas.lasreader.LasReader

    """
    if isinstance(source, str):
        stream = open(source, mode='rb')
        if not closefd:
            raise ValueError("Cannot use closefd with filename")
    else:
        stream = source
    return LasReader(stream, closefd=closefd)


def read_las(source, closefd=True):
    """ Entry point for reading las data in pylas

    Reads the whole file in memory.

    Parameters
    ----------
    source : {str | file_object}
        The source to read data from

    Returns
    -------
    pylas.lasdatas.base.LasBase
        The object you can interact with to get access to the LAS points & VLRs
    """
    with open_las(source, closefd=closefd) as reader:
        return reader.read()


def mmap_las(filename):
    return LasMMAP(filename)


def create_from_header(header):
    points = record.PackedPointRecord.zeros(header.point_data_format_id, header.point_count)
    if header.version >= '1.4':
        return las14.LasData(header=header, points=points)
    return las12.LasData(header=header, points=points)


def create_las(*, point_format=0, file_version=None):
    """ Function to create a new las data object

    .. note::

        If you provide both point_format and file_version
        an exception will be raised if they are not compatible

    >>> las = create_las(point_format=6, file_version="1.2")
    Traceback (most recent call last):
     ...
    ValueError: Point format 6 is not compatible with file version 1.2


    If you provide only the point_format the file_version will automatically
    selected for you.

    >>> las = create_las(point_format=0)
    >>> las.header.version == '1.2'
    True

    >>> las = create_las(point_format=6)
    >>> las.header.version == '1.4'
    True


    Parameters
    ----------
    point_format : int, optional, default=0
        The point format you want the resulting las to have
    file_version: str, optional, default=None
        The las version you want the created las to have

    Returns
    -------
    pylas.lasdatas.base.LasBase
       A new las data object

    """
    if file_version is not None and not dims.is_point_fmt_compatible_with_version(point_format, file_version):
        raise ValueError('Point format {} is not compatible with file version {}'.format(
            point_format, file_version
        ))
    else:
        file_version = dims.min_file_version_for_point_format(point_format)

    header = headers.HeaderFactory.new(file_version)
    header.point_data_format_id = point_format

    if file_version >= '1.4':
        return las14.LasData(header=header)
    return las12.LasData(header=header)


def convert(source_las, *, point_format_id=None, file_version=None):
    """ Converts a Las from one point format to another
    Automatically upgrades the file version if source file version is not compatible with
    the new point_format_id


    convert to point format 0

    >>> las = read_las('pylastests/simple.las')
    >>> las.header.version
    '1.2'
    >>> las = convert(las, point_format_id=0)
    >>> las.header.version
    '1.2'

    convert to point format 6, which need version >= 1.4
    then convert back to point format 0, version is not downgraded

    >>> las = read_las('pylastests/simple.las')
    >>> las.header.version
    '1.2'
    >>> las = convert(las, point_format_id=6)
    >>> las.header.version
    '1.4'
    >>> las = convert(las, point_format_id=0)
    >>> las.header.version
    '1.4'

    an exception is raised if the requested point format is not compatible
    with the file version

    >>> las = read_las('pylastests/simple.las')
    >>> convert(las, point_format_id=6, file_version='1.2')
    Traceback (most recent call last):
     ...
    ValueError: Point format 6 is not compatible with file version 1.2

    Parameters
    ----------
    source_las : {LasData}
        The source data to be converted

    point_format_id : {int}, optional
        The new point format id (the default is None, which won't change the source format id)

    file_version : str, optional,
        The new file version. None by default which means that the file_version
        may be upgraded for compatibility with the new point_format. The file version will not
        be downgraded.

    Returns
    -------
        LasData
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

    header = headers.HeaderFactory.convert_header(source_las.header, file_version)
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
