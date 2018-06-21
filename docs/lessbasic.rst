=================
Less Basic Things
=================


Extra Dimensions
================

The LAS Specification version 1.4 defines a standard way to add extra dimensions to
a LAS file.

In pylas you can add extra dimensions using the :meth:`pylas.lasdatas.las14.LasData.add_extra_dim` function


The Allowed base types for an extra dimensions are:

+-------------------------+-------------+-------------+
|       pylas name        | size (bits) |     type    |
+=========================+=============+=============+
|     u1 or uint8         |     8       |  unsigned   |
+-------------------------+-------------+-------------+
|     i1 or int8          |     8       |   signed    |
+-------------------------+-------------+-------------+
|     u2 or uint16        |     16      |   unsigned  |
+-------------------------+-------------+-------------+
|     i2 or int16         |     16      |    signed   |
+-------------------------+-------------+-------------+
|     u4 or uint32        |     32      |   unsigned  |
+-------------------------+-------------+-------------+
|     i4 or int32         |     32      |    signed   |
+-------------------------+-------------+-------------+
|     u8 or uint64        |     64      |   unsigned  |
+-------------------------+-------------+-------------+
|     i8 or int64         |     64      |    signed   |
+-------------------------+-------------+-------------+
|     f4 or float         |     32      |   floating  |
+-------------------------+-------------+-------------+
|     f8 or double        |     64      |   floating  |
+-------------------------+-------------+-------------+

You can prepend the number '2' or '3' to one of the above base type to define an extra dimension
that is array of 2 or 3 elements per points.
Example: 3u2 -> each points will have an extra dimension that is an array of 3 * 16 bits


Here we are adding a new dimension called "codification" where each value is stored on a 64 bit unsigned integer
and an array field of 3 doubles for each points.


.. code-block:: python

    import pylas
    las = pylas.read("somefile.las")

    las.add_extra_dim(name="codification", type="uint64", description="More classes available")

    las.add_extra_dim(name="mysterious", type="3f8")




.. note::

    As the specification of the ExtraBytesVlr appeared in the 1.4 LAS Spec, pylas restrict the ability to
    add new dimensions to file with version >= 1.4 even if it would be totally possible to define new dimension
    on older versions.
    (Maybe this should change?)