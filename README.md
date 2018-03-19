# pylas
Another way of reading Las in Python

``` python
import pylas

las = pylas.open('filename.las')
las = pylas.convert(las, point_format_id=2)
las.write('converted.laz')

```
