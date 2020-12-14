import pylas
import sys

import logging

logging.basicConfig(level=logging.INFO)

sys.path.append(r"C:\Users\Thomas\Projects\laszipy\cmake-build-debug")

# path = "pylastests/simple.laz"
path = r"E:\laz-rz-test-data\philadelphia-2015-fmt3\26502E1932N.laz"

las = pylas.read(path, laz_backend=pylas.LazBackend.Laszip)
print(las.intensity)

las.write("test.laz", laz_backend=pylas.LazBackend.Laszip)

las = pylas.read(path, laz_backend=pylas.LazBackend.Lazrs)
print(las.intensity)

las = pylas.read("test.laz", laz_backend=pylas.LazBackend.Lazrs)
print(las.intensity)
