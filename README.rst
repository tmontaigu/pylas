pylas
-----

Another way of reading point clouds in the LAS/LAZ in Python.

.. image:: https://readthedocs.org/projects/pylas/badge/?version=latest
    :target: https://pylas.readthedocs.io/en/latest/?badge=latest
    :alt: Documentation Status

.. image:: https://travis-ci.org/tmontaigu/pylas.svg?branch=master


Examples
--------

Directly read and write las

.. code:: python

    import pylas

    las = pylas.read('filename.las')
    las.points = las.points[las.classification == 2]
    las.write('ground.laz')

Open data to inspect header (opening only reads the header and vlrs)

.. code:: python

    import pylas

    with pylas.open('filename.las') as f:
        print(f"Point format:       {f.header.point_format}")
        print(f"Number of points:   {f.header.point_count}")
        print(f"Number of vlrs:     {len(f.header.vlrs)}")

Use the 'chunked' reading & writing features

.. code:: python

    import pylas

    with pylas.open('big.laz') as input_las:
        with pylas.open('ground.laz', mode="w", header=input_las.header) as ground_las:
            for points in input_las.chunk_iterator(2_000_000):
                ground_las.write_points(points[points.classification == 2])

Appending points to existing file

.. code:: python

    import pylas

    with pylas.open('big.laz') as input_las:
        with pylas.open('ground.laz', mode="a") as ground_las:
            for points in input_las.chunk_iterator(2_000_000):
                ground_las.append_points(points[points.classification == 2])

Documentation
-------------

Documentation is hosted on ReadTheDocs_ .

.. _ReadTheDocs: http://pylas.readthedocs.io/en/latest/index.html


Dependencies & Requirements
---------------------------

Supported CPython versions are: 3.6, 3.7, 3.8, 3.9

pylas supports LAS natively, to support LAZ it needs one of its supported backend to be installed:

- lazrs
- laszip


Installation
------------

.. code-block:: shell

    pip install pylas # without LAZ support
    # Or
    pip install pylas[laszip] # without LAZ support via LASzip
    # Or
    pip install pylas[lazrs] # without LAZ support via lazrs


See the Installation_ section of the documentation for details:

.. _Installation: https://pylas.readthedocs.io/en/latest/installation.html

