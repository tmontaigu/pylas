============
Installation
============

Installing from PyPi
====================

.. code:: shell

    pip install pylas


Optional dependencies for LAZ support
=====================================

pylas does not support LAZ (.laz) file by itself but can use one of several optional dependencies
to support compressed LAZ files.

The 2 supported options are:

1) `lazrs`_ `[lazrs PyPi]`_
3) `laszip.exe`_

When encountering LAZ data, pylas will try this options in the order described above.
(Example: if lazrs is not installed or if it fails during, the process, pylas will try laszip)

`lazrs`_ is a Rust port of the laszip compression and decompression.
Its main advantage is that it is able to compress/decompress using multiple threads which can
greatly speed up things.

`laszip.exe`_  is the laszip executable from the original LAZ implementation found in `LAStools`_
The advandage of `laszip.exe` is that its the official implementation, however due to the way it is
used (pylas uses a python Popen and talks to the laszip exe via its stdin, stdout) there is some overhead
giving slower compression / decompression times and a bit higher memory usage.


lazrs is available on pypi and can be installed via pip, for LAStools's laszip
you have to either compile it yourself, download it from lastools website.

You can `pip install` lazrs by yourself.

Or use pip extra_requires (since pylas 0.4.0)

.. code-block:: shell

    pip install pylas[lazrs]

.. _lazrs: https://github.com/tmontaigu/laz-rs
.. _LAStools: https://rapidlasso.com/lastools/
.. _laszip.exe: https://rapidlasso.com/lastools/
.. _[lazrs PyPi]: https://pypi.org/project/lazrs/





