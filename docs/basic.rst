==================
Basic Manipulation
==================


Opening & Reading
=================
You have two ways to read LAS files with pylas.

The easiest one is using :func:`pylas.read` function.
This function will read everything in the file (Header, vlrs, point records, ...) and return an object
that you can use to access to the data.

.. code:: python

    las = pylas.read('somefile.las')
    print(np.unique(las.classification))

    import s3fs
    fs = s3fs.S3FileSystem()
    with fs.open('my-bucket/some_file.las', 'rb') as f:
         las = pylas.read(f)


The other way to read a las file is to use the :func:`pylas.open`.
As the name suggest, this function does not read the whole file, but opens it and only read the header.

This is useful if you only need to read the header without loading the whole file in memory.


Converting
==========

pylas also offers the ability to convert a file between the different version and point format available
(as long as they are compatible).

To convert, use the :func:`pylas.convert`

Creating
========

Creating a new Las from scratch is simple.
Use :func:`pylas.create`.


Writing
=======

To be able to write a las file you will need a :class:`pylas.lasdatas.base.LasBase` (or one if its subclasses).
You obtain this type of object by using one of the function above,
use its method :meth:`pylas.lasdatas.base.LasBase.write` to write to a file or a stream.

.. _accessing_header:

Accessing the file header
=========================

You can access the header of a las file you read or opened by retrieving the 'header' attribute:

>>> import pylas
>>> las = pylas.read('pylastests/simple.las')
>>> las.header
<LasHeader(1.2)>
>>> las.header.point_count
1065


>>> with pylas.open('pylastests/simple.las') as f:
...     f.header.point_count
1065



you can see the accessible fields in :class:`pylas.headers.rawheader.RawHeader1_1` and its sub-classes.


Accessing Points Records
========================

To access point records using the dimension name, you have 2 options:

1) regular attribute access using the `las.dimension_name` syntax
2) dict-like attribute access `las[dimension_name]`.

>>> import numpy as np
>>> las = pylas.read('pylastests/simple.las')
>>> np.all(las.user_data == las['user_data'])
True

However if you wish to retrieve the x, y, z coordinates with scale and offset applied
your only option is the first method.

>>> las.x.max().dtype
dtype('float64')

The dimensions available in a file are dictated by the point format id.
The tables in the introduction section contains the list of dimensions for each of the
point format.
To get the point format of a file you have to access it through the points_data member:

>>> point_format = las.points_data.point_format
>>> point_format
<PointFormat(3)>
>>> point_format.id
3

If you don't want to rember the dimensions for each point format,
you can access the list of available dimensions in the file you read just like that:

>>> point_format.dimension_names
('X', 'Y', 'Z', 'intensity', 'return_number', 'number_of_returns', 'scan_direction_flag', 'edge_of_flight_line', 'classification', 'synthetic', 'key_point', 'withheld', 'scan_angle_rank', 'user_data', 'point_source_id', 'gps_time', 'red', 'green', 'blue')

This gives you all the dimension names, including extra dimensions if any.
If you wish to get only the extra dimension names the point format can give them to you:

>>> point_format.extra_dimension_names
[]
>>> las = pylas.read('pylastests/extra.laz')
>>> las.points_data.point_format.extra_dimension_names
['Colors', 'Reserved', 'Flags', 'Intensity', 'Time']

.. _manipulating_vlrs:

Manipulating VLRs
=================

To access the VLRs stored in a file, simply access the `vlr` member of the las object.

>>> las = pylas.read('pylastests/extrabytes.las')
>>> las.vlrs
[<ExtraBytesVlr(extra bytes structs: 5)>]

>>> with pylas.open('pylastests/extrabytes.las') as f:
...     vlr_list = f.read_vlrs()
>>> vlr_list
[<ExtraBytesVlr(extra bytes structs: 5)>]


To retrieve a particular vlr from the list there are 2 ways: :meth:`pylas.vlrs.vlrlist.VLRList.get` and
:meth:`pylas.vlrs.vlrlist.VLRList.get_by_id`