import pylas
import io
import numpy as np
from pylas import LazBackend
import logging

from pylas.lib import write_then_read_again
from pylas.vlrs.vlrlist import VLRList


# las = pylas.read("pylastests/test1_4.las")
# las.vlrs = VLRList()
# assert las.evlrs == []
#
# evlr = pylas.EVLR(user_id="pylastest", record_id=42, description="Just a test")
# evlr.record_data = b"While he grinds his own hands"
# las.evlrs.append(evlr)
#
# # las.points = las.points[:1]
# # las = write_then_read_again(las, do_compress=True)
# #
# name = "with_evlr_no_vlrs.laz"
# las.write(name)
#
#
# def print_header(path):
#     print("-" * 80)
#     # with pylas.open(path, laz_backends=[LazBackend.Laszip]) as f:
#     #     print("version", f.header.version)
#     #     print("point count", f.header.point_count)
#     #     print("compressed:", f.header.are_points_compressed)
#     #     print("num_vlrs:", f.header.number_of_vlr)
#     #     print("offset to points", f.header.offset_to_point_data)
#     #     print("evlrs", f.header.number_of_evlr)
#     #     print("start evlrs", f.header.start_of_first_evlr)
#
#     with open(path, mode='rb') as file:
#         header = pylas.HeaderFactory.read_from_stream(file)
#         print("version", header.version)
#         print("point count", header.point_count)
#         print("compressed:", header.are_points_compressed)
#         print("num_vlrs:", header.number_of_vlr)
#         print("offset to points", header.offset_to_point_data)
#         print("evlrs", header.number_of_evlr)
#         print("start evlrs", header.start_of_first_evlr)
#         print("size", header.size)
#         print("point_data_record_length", header.point_data_record_length)
#         print("legacy_point_count", header.legacy_point_count)
#         print("legacy_number_of_points_by_return", list(header.legacy_number_of_points_by_return))
#         print("scales", header.scales)
#         print("offsets", header.offsets)
#         print("max", header.maxs)
#         print("min", header.mins)
#
#         file.seek(header.offset_to_point_data)
#         offset_to_chunk_table = int.from_bytes(file.read(8), 'little', signed=True)
#         print("offset to chunk_table", offset_to_chunk_table)
#
#
# with open(name, mode='rb') as f:
#     b1 = f.read()
#
# with open("pylastests/groundtruth.laz", mode='rb') as f:
#     b2 = f.read()
#
# print(len(b1), len(b2))
#
# for i, (c, cc) in enumerate(zip(b1, b2)):
#     if c != cc:
#         print(f"bytes {i} are not equal")
#
# print_header(name)
# print_header("pylastests/groundtruth.laz")

# with io.BytesIO() as o:
#     las.write_to(o, do_compress=True)
#
#     with open("ayaya.laz", mode="wb") as f:
#         f.write(o.getvalue())
# with open("pylastests/groundtruth.laz", mode='rb') as f:
#     b = f.read()
#     # for b in f:
#     #     print(len(b))
# las = pylas.read(b)
#las = pylas.read("with_evlr_no_vlrs.laz")
with pylas.open("pylastests/groundtruth.laz", laz_backends=[LazBackend.Laszip]) as f:
    print("opened now reading")
    f.read()
