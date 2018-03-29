# pylas

Another way of reading LAS/LAZ in Python.

## Example

```python
import pylas

# Directly read and write las 
las = pylas.read('filename.las')
las = pylas.convert(point_format_id=2)
las.write('converted.las')

# Open data to inspect header and then read
with pylas.open('filename.las') as f:
    if f.header.number_of_point_records < 10 ** 8:
        las = f.read()

```

## Dependencies



## Installation

Usual python installation:

```python
python setup.py install
```

