==================
Basic Manipulation
==================


Opening & Reading
=================
You have two ways to read LAS files with pylas.

The easiest one is using ``pylas.read`` function, which is a shortcut to :func:`pylas.lib.read_las`
This function will read everything in the file (Header, vlrs, point records, ...) and return an object
that you can use to access to the data.


The other way to read a las file is to use the ``pylas.open`` which is a shortcut for :func:`pylas.lib.open_las`
As the name suggest, this function does not read the whole file, but opens it and only read the header.

This is useful if you only need to read the header without loading the whole file in memory.



Converting
==========

pylas also offers the ability to convert a file between the different version and point format available
(as long as they are compatible).

To convert, use the ``pylas.convert``, again a shortcut for :func:`pylas.lib.convert`

Creating
========

Creating a new Las from scratch is simple.
Use the ``pylas.create`` (:func:`pylas.lib.create_las`)


Writing
=======

To be able to write a las file you will need a :class:`pylas.lasdatas.base.LasBase` (or one if its subclasses).
You obtain this type of object by using one of the function above,
use its method :meth:`pylas.lasdatas.base.LasBase.write` to write to a file or a stream.


