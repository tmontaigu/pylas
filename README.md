# pylas
Another way of reading Las in Python

``` python
import pylas

las = pylas.read('filename.las')
las = pylas.convert(point_format_id=2)
las.write('converted.las')

with pylas.open('filename.las') as f:
    if f.header.number_of_point_records < 10 ** 8:
        las = f.read()

```
