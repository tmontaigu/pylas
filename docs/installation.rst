============
Installation
============

Dependencies
============

pylas does not require, but greatly benefits from `laz perf`_.
Lazperf is an alternative LAZ implementation, with Python bindings available which allows
pylas to read and compress LAZ.

Currently (30th March 2018) laz-perf supports compressing and decompressing point formats 0, 1, 2, 3.

pylas can also use `LAStools's`_ laszip cli to decompress (only).
pylas will try to use laszip if laz-perf is not installed, or if laz-perf fails to decompress a file
(for example when laz-perf does not know how to decompress the point format).
However laszip cannot currently be used by pylas to compress data.

.. _laz perf: https://github.com/hobu/laz-perf
.. _LAStools's: https://rapidlasso.com/lastools/


Installing from source
======================

.. code:: shell

    pip install pylas




