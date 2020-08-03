import pylas
import io
import numpy as np
from pylas import LazBackend
import logging

logging.basicConfig(level=logging.INFO)

# file_path = r"L:\LAS\technicentre\ROBIN_BDX_TechnicentreVF.laz"
# file_path = r"C:\Users\t.montaigu\Projects\pylas\pylastests\simple.laz"
file_path = r"L:\LAS\1.2\Talence\R1_F_0+000_0+050.laz"

# print("_" * 80)
# print("laz")
# with pylas.open(file_path, laz_backends=[pylas.LazBackend.Laszip]) as reader:
#     print(reader)
#     with pylas.open("output.laz",  mode="w", header=reader.header, laz_backends=[pylas.LazBackend.LazrsParallel]) as writer:
#         print(writer.point_format)
#         for points in reader.chunk_iterator(50):
#             print(points.x)
#             writer.write(points)
#
# print("_" * 80)
# with pylas.open("output.laz", laz_backends=[LazBackend.Laszip]) as f:
#     print(f.header.are_points_compressed)
#     print(f.header.point_count)
#     print(f.header.number_of_points_by_return[:])
#     las = f.read()
#     print(las)




# file_path = r"L:\LAS\1.2\Talence\R1_F_0+000_0+050.laz"
# LAS = pylas.read(r"L:\LAS\1.2\Talence\R1_F_0+000_0+050.las")
#
# with pylas.open(file_path, laz_backends=[pylas.LazBackend.LazrsParallel]) as reader:
#     print("Num pts: {}".format(reader.header.point_count))
#     iter_size = 500_001
#     for i, points in enumerate(reader.chunk_iterator(iter_size)):
#         print(f"Chunk number {i}")
#         expected_pts = LAS.points[i * iter_size:(i + 1) * iter_size]
#         for name in points.array.dtype.names:
#             assert np.allclose(points[name], expected_pts[name]), f"{name} dims are not equal"

laz_path = r"C:\Users\t.montaigu\Projects\pylas\pylastests\simple.laz"
las_path = r"C:\Users\t.montaigu\Projects\pylas\pylastests\simple.las"

# laz_path = r"L:\LAS\1.2\Talence\R1_F_0+000_0+050.laz"
# las_path = r"L:\LAS\1.2\Talence\R1_F_0+000_0+050.las"

with pylas.open(laz_path, laz_backends=[LazBackend.Laszip]) as reader:
    print("Num pts: {}".format(reader.header.point_count))
    iter_size = 456_154

    with pylas.open("output.laz", mode="w", header=reader.header, laz_backends=[LazBackend.Laszip]) as output:
        for i, points in enumerate(reader.chunk_iterator(iter_size)):
            output.write(points)

print("Reading back my file")
with pylas.open("output.laz", laz_backends=[LazBackend.LazrsParallel]) as reader:
    print("ab", reader.header.number_of_vlr)
    iter_size = 500_001
    hdr = reader.header
    print(hdr.number_of_vlr)
    for i, points in enumerate(reader.chunk_iterator(iter_size)):
        print(points)
