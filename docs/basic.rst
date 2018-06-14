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
         las = pylas.read()


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



Manipulating VLRs
=================

To access the VLRs stored in a file, simply access the `vlr` member of the las object.

.. code:: python

    las = pylas.read('somefile.las')
    vlr_list = las.vlrs

    # or

    with pylas.open('somefile.las') as f:
        vlr_list = f.read_vlrs()


To retrieve a particular vlr from the list there are 2 ways: :meth:`pylas.vlrs.vlrlist.VLRList.get` and
:meth:`pylas.vlrs.vlrlist.VLRList.get_by_id`