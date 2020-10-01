""" 'Entry point' of the library, Contains the various functions meant to be
used directly by a user
"""
import copy
import io
import logging
import os
from pathlib import Path
from typing import Union

import numpy as np

from . import headers, utils
from .compression import LazBackend
from .errors import PylasError
from .lasdatas import las12, las14
from .lasmmap import LasMMAP
from .lasreader import LasReader
from .laswriter import LasWriter
from .lasappender import LasAppender
from .point import dims, record, PointFormat

logger = logging.getLogger(__name__)


def open_las(
    source,
    mode="r",
    closefd=True,
    laz_backend=LazBackend.detect_available(),
    header=None,
    do_compress=None,
) -> Union[LasReader, LasWriter, LasAppender]:
    """Opens and reads the header of the las content in the source

        >>> with open_las('pylastests/simple.las') as f:
        ...     print(f.header.point_format_id)
        3


        >>> f = open('pylastests/simple.las', mode='rb')
        >>> with open_las(f,closefd=False) as flas:
        ...     print(flas.header)
        <LasHeader(1.2)>
        >>> f.closed
        False
        >>> f.close()
        >>> f.closed
        True


        >>> f = open('pylastests/simple.las', mode='rb')
        >>> with open_las(f) as flas:
        ...    las = flas.read()
        >>> f.closed
        True

    Parameters
    ----------
    source: str or bytes or io.BytesIO
        if source is a str it must be a filename
        a stream if a file object with the methods read, seek, tell

    mode: Optional, the mode to open the file "r" for reading, "w" for writing
          "r" by default

    laz_backend: Optional, the LAZ backend to use to handle decompression/comression
                 By default available_backends are detected, see LazBacked to see the
                 preference order when multiple backends are available

    header: The header to use when opening in write mode.

    do_compress: optional, bool
                 -> None (default) guess if compression is needed using the file extension
                 -> True compresses the file
                 -> False do not compress the file

    closefd: bool
        Whether the stream/file object shall be closed, this only work
        when using open_las in a with statement. An exception is raised if
        closefd is specified and the source is a filename


    Returns
    -------
    pylas.lasreader.LasReader

    """
    if mode == "r":
        if header is not None:
            raise PylasError(
                "header argument is not used when opening in read mode, "
                "did you meant to open in write mode ?"
            )
        if do_compress is not None:
            raise PylasError(
                "do_compress argument is not used when opening in read mode, "
                "did you meant to open in write mode ?"
            )
        if isinstance(source, (str, Path)):
            stream = open(source, mode="rb", closefd=closefd)
        elif isinstance(source, bytes):
            stream = io.BytesIO(source)
        else:
            stream = source
        return LasReader(stream, closefd=closefd, laz_backend=laz_backend)
    elif mode == "w":
        if header is None:
            raise ValueError("A header is needed when opening a file for writing")

        if isinstance(source, (str, Path)):
            if do_compress is None:
                do_compress = os.path.splitext(source)[1].lower() == ".laz"
            stream = open(source, mode="wb+", closefd=closefd)
        elif isinstance(source, bytes):
            stream = io.BytesIO(source)
        else:
            assert source.seekable()
            stream = source
        if do_compress is None:
            do_compress = False
        return LasWriter(
            stream,
            header=header,
            do_compress=do_compress,
            laz_backend=laz_backend,
            closefd=closefd,
        )
    elif mode == "a":
        if isinstance(source, (str, Path)):
            stream = open(source, mode="rb+", closefd=closefd)
        elif isinstance(source, bytes):
            stream = io.BytesIO(source)
        else:
            stream = source
        return LasAppender(stream, closefd=closefd, laz_backend=laz_backend)

    else:
        raise ValueError("Unknown mode '{}'".format(mode))


def read_las(source, closefd=True, laz_backend=LazBackend.detect_available()):
    """Entry point for reading las data in pylas

    Reads the whole file into memory.

    >>> las = read_las("pylastests/simple.las")
    >>> las.classification
    <SubFieldView([1 1 1 ... 1 1 1])>

    Parameters
    ----------
    source : str or io.BytesIO
        The source to read data from

    laz_backend: Optional, the backend to use when the file is as LAZ file.
                 By default pylas will find the backend to use by himself.
                 Use if you wan a specific backend to be used

    closefd: bool
            if True and the source is a stream, the function will close it
            after it is done reading


    Returns
    -------
    pylas.lasdatas.base.LasBase
        The object you can interact with to get access to the LAS points & VLRs
    """
    with open_las(source, closefd=closefd, laz_backend=laz_backend) as reader:
        return reader.read()


def mmap_las(filename):
    """MMap a file, much like laspy did, very experimental
    not well tested
    """
    return LasMMAP(filename)


def create_from_header(header):
    """Creates a File from an existing header,
    allocating the array of point according to the provided header.
    The input header is copied.


    Parameters
    ----------
    header : existing header to be used to create the file

    Returns
    -------
    pylas.lasdatas.base.LasBase
    """
    header = copy.copy(header)
    header.point_count = 0
    points = record.PackedPointRecord.empty(PointFormat(header.point_format_id))
    if header.version >= "1.4":
        return las14.LasData(header=header, points=points)
    return las12.LasData(header=header, points=points)


def create_las(*, point_format_id=0, file_version=None):
    """Function to create a new empty las data object

    .. note::

        If you provide both point_format and file_version
        an exception will be raised if they are not compatible

    >>> las = create_las(point_format_id=6,file_version="1.2")
    Traceback (most recent call last):
     ...
    pylas.errors.PylasError: Point format 6 is not compatible with file version 1.2


    If you provide only the point_format the file_version will automatically
    selected for you.

    >>> las = create_las(point_format_id=0)
    >>> las.header.version == '1.2'
    True

    >>> las = create_las(point_format_id=6)
    >>> las.header.version == '1.4'
    True


    Parameters
    ----------
    point_format_id: int
        The point format you want the created file to have

    file_version: str, optional, default=None
        The las version you want the created las to have

    Returns
    -------
    pylas.lasdatas.base.LasBase
       A new las data object

    """
    if file_version is not None:
        dims.raise_if_version_not_compatible_with_fmt(point_format_id, file_version)
    else:
        file_version = dims.min_file_version_for_point_format(point_format_id)

    header = headers.HeaderFactory.new(file_version)
    header.point_format_id = point_format_id

    if file_version >= "1.4":
        return las14.LasData(header=header)
    return las12.LasData(header=header)


def convert(source_las, *, point_format_id=None, file_version=None):
    """Converts a Las from one point format to another
    Automatically upgrades the file version if source file version is not compatible with
    the new point_format_id


    convert to point format 0

    >>> las = read_las('pylastests/simple.las')
    >>> las.header.version
    '1.2'
    >>> las = convert(las, point_format_id=0)
    >>> las.header.point_format_id
    0
    >>> las.header.version
    '1.2'

    convert to point format 6, which need version >= 1.4
    then convert back to point format 0, version is not downgraded

    >>> las = read_las('pylastests/simple.las')
    >>> las.header.version
    '1.2'
    >>> las = convert(las, point_format_id=6)
    >>> las.header.point_format_id
    6
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
    pylas.errors.PylasError: Point format 6 is not compatible with file version 1.2

    Parameters
    ----------
    source_las : pylas.lasdatas.base.LasBase
        The source data to be converted

    point_format_id : int, optional
        The new point format id (the default is None, which won't change the source format id)

    file_version : str, optional,
        The new file version. None by default which means that the file_version
        may be upgraded for compatibility with the new point_format. The file version will not
        be downgraded.

    Returns
    -------
        pylas.lasdatas.base.LasBase
    """
    if point_format_id is None:
        point_format_id = source_las.point_format.id

    if file_version is None:
        file_version = max(
            source_las.header.version,
            dims.min_file_version_for_point_format(point_format_id),
        )
    else:
        file_version = str(file_version)
        dims.raise_if_version_not_compatible_with_fmt(point_format_id, file_version)

    header = headers.HeaderFactory.convert_header(source_las.header, file_version)
    header.point_format_id = point_format_id

    point_format = PointFormat(point_format_id)
    point_format.dimensions.extend(source_las.point_format.extra_dimensions)
    points = record.PackedPointRecord.from_point_record(source_las.points, point_format)

    try:
        evlrs = source_las.evlrs
    except AttributeError:
        evlrs = []

    if file_version >= "1.4":

        las = las14.LasData(
            header=header, vlrs=source_las.vlrs, points=points, evlrs=evlrs
        )
    else:
        if evlrs:
            logger.warning(
                "The source contained {} EVLRs,"
                " they will be lost as version {} doest not support them".format(
                    len(evlrs), file_version
                )
            )
        las = las12.LasData(header=header, vlrs=source_las.vlrs, points=points)

    return las


def merge_las(*las_files):
    """Merges multiple las files into one

    merged = merge_las(las_1, las_2)
    merged = merge_las([las_1, las_2, las_3])

    Parameters
    ----------
    las_files: Iterable of LasData or LasData

    Returns
    -------
    pylas.lasdatas.base.LasBase
        The result of the merging

    """
    if len(las_files) == 1:
        las_files = las_files[0]

    if not las_files:
        raise ValueError("No files to merge")

    if not utils.files_have_same_dtype(las_files):
        raise ValueError("All files must have the same point format")

    header = las_files[0].header
    num_pts_merged = sum(len(las.points) for las in las_files)

    # scaled x, y, z have to be set manually
    # to be sure to have a good offset in the header
    merged = create_from_header(header)
    # TODO extra dimensions should be managed better here

    for dim_name, dim_type in las_files[0].points.point_format.extra_dims:
        merged.add_extra_dim(dim_name, dim_type)

    merged.points = np.zeros(num_pts_merged, merged.points.dtype)
    merged_x = np.zeros(num_pts_merged, np.float64)
    merged_y = np.zeros(num_pts_merged, np.float64)
    merged_z = np.zeros(num_pts_merged, np.float64)

    offset = 0
    for i, las in enumerate(las_files, start=1):
        slc = slice(offset, offset + len(las.points))
        merged.points[slc] = las.points
        merged_x[slc] = las.x
        merged_y[slc] = las.y
        merged_z[slc] = las.z
        merged["point_source_id"][slc] = i
        offset += len(las.points)

    merged.x = merged_x
    merged.y = merged_y
    merged.z = merged_z

    return merged


def write_then_read_again(
    las, do_compress=False, laz_backend=LazBackend.detect_available()
):
    """writes the given las into memory using BytesIO and
    reads it again, returning the newly read file.

    Mostly used for testing purposes, without having to write to disk
    """
    out = io.BytesIO()
    las.write(out, do_compress=do_compress, laz_backend=laz_backend)
    out.seek(0)
    return read_las(out)
