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
    las = pylas.convert(las, point_format_id=2)
    las.write('converted.las')

    # Open data to inspect header and then read
    with pylas.open('filename.las') as f:
        if f.header.point_count < 10 ** 8:
            las = f.read()
    print(las.vlrs)

Documentation is hosted on ReadTheDocs_ .

.. _ReadTheDocs: http://pylas.readthedocs.io/en/latest/index.html


Installation
------------

See the Installation_ section of the documentation:

.. _Installation: https://pylas.readthedocs.io/en/latest/installation.html

Dependencies & Requirements
---------------------------

Supported CPython versions are: 3.6, 3.7, 3.8, 3.9

pylas supports LAS natively,to support LAZ it needs one of its supported backend to be installed:

 - lazrs
 - laszip


Installation
------------

::

    pip install pylas


