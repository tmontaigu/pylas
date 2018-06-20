pylas
-----

Another way of reading LAS/LAZ in Python.

.. image:: https://readthedocs.org/projects/pylas/badge/?version=latest
    :target: https://pylas.readthedocs.io/en/latest/?badge=latest
    :alt: Documentation Status


.. image:: https://travis-ci.org/tmontaigu/pylas.svg?branch=master

Example
-------

.. code:: python

    import pylas

    # Directly read and write las 
    las = pylas.read('filename.las')
    las = pylas.convert(point_format_id=2)
    las.write('converted.las')

    # Open data to inspect header and then read
    with pylas.open('filename.las') as f:
        if f.header.point_count < 10 ** 8:
            las = f.read()
    print(las.vlrs)

Some rough documentation is available on ReadTheDocs_ .

.. _ReadTheDocs: http://pylas.readthedocs.io/en/latest/index.html

Dependencies & Requirements
---------------------------

Python 3 Only.

lazperf_ is an optional, but recommended dependency that allows pylas to read and write compressed LAZ files.

.. _lazperf: https://github.com/hobu/laz-perf



Installation
------------

::

    pip install pylas


