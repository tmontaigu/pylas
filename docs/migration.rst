Migration guides
================

From 0.4.x to 1.0.0
-------------------

Changes in LAZ backend
______________________

With pylas 1.0.0, the lazperf backend
support was dropped, and the laszip backend
changed from using the laszip executable
to using laszip python bindings.

If you used lazperf or relied on the laszip executable
you'll have to choose between the available backends.
(see Installation section).


Changes in bit fields
_____________________

Some fields in LAS are 'bit fields'.

with pylas 0.4.x, there was a inconsistency between
'normal' fields and 'bit' fields, when getting a bit field,
pylas returned a copy of the values in a new numpy array whereas
when getting a normal field, the array you got acted as a 'view'
on the real array where the values where stored.

That meant that modifying the values of the array you got from
a bit field would no propagate to the real array.

.. code-block:: python

    import pylas
    import numpy as np

    las = pylas.read("pylastests/simple.las")

    # return number is a bit field
    print(las.return_number)
    # array([1, 1, 1, ..., 1, 1, 1], dtype=uint8)

    ascending_order = np.argsort(las.return_number)[::-1]
    print(las.return_number[ascending_order])
    # array([4, 4, 4, ..., 1, 1, 1], dtype=uint8)
    las.return_number[:] = las.return_number[ascending_order]
    print(las.return_number)
    # array([1, 1, 1, ..., 1, 1, 1], dtype=uint8) # bif oof
    las.return_number[0] = 7
    print(las.return_number)
    # array([1, 1, 1, ..., 1, 1, 1], dtype=uint8) # again value not updated


    # To actually update you have to do
    las.return_number = las.return_number[ascending_order]
    print(las.return_number)
    # array([4, 4, 4, ..., 1, 1, 1], dtype=uint8)

    rn = las.return_number[ascending_order]
    rn[0] = 7
    las.return_number = rn
    print(las.return_number)
    # array([7, 4, 4, ..., 1, 1, 1], dtype=uint8)



In order to try to solve this inconsistency, pylas >= 0.5.0
introduced the :class:`.SubFieldView` class that is meant to propagate
modifications to the real array, and tries to act like a real numpy array.

.. code-block:: python

    import pylas
    import numpy as np

    las = pylas.read("pylastests/simple.las")

    print(las.return_number)
    # <SubFieldView([1 1 1 ... 1 1 1])>

    ascending_order = np.argsort(las.return_number)[::-1]
    las.return_number[:] = las.return_number[ascending_order]
    print(las.return_number)
    # <SubFieldView([4 4 4 ... 1 1 1])>
    las.return_number[0] = 7
    print(las.return_number)
    # <SubFieldView([7 4 4 ... 1 1 1])>

It may be possible that some operation on SubFieldView fail, in that case
it is easy to copy them to numpy arrays:

.. code-block:: python


    import pylas
    import numpy as np

    las = pylas.read("pylastests/simple.las")
    print(las.return_number)
    # <SubFieldView([1 1 1 ... 1 1 1])>

    array = np.array(las.return_number)
    # array([1, 1, 1, ..., 1, 1, 1], dtype=uint8)

