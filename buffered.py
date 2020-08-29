import numpy as np

import pylas
from pathlib import Path
import argparse
import io


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("path")
    parser.add_argument("--ilaz", default=None)
    parser.add_argument("--olaz", default=None)

    args = parser.parse_args()

    if args.olaz is not None:
        olaz_backend = (getattr(pylas.LazBackend, args.olaz),)
        do_compress = True
    else:
        olaz_backend = None
        do_compress = False

    if args.ilaz is not None:
        ilaz_backend = (getattr(pylas.LazBackend, args.ilaz),)
        all_files = Path(args.path).rglob("*.la[sz]")
    else:
        ilaz_backend = None
        all_files = Path(args.path).rglob("*.las")

    for file_path in all_files:
        print(f"checking {file_path}")
        # with io.BytesIO() as output:
        # # with open('lol.laz', mode="w+b") as output:
        #     with pylas.open(str(file_path), laz_backends=ilaz_backend) as las_file:
        #         with pylas.open(output,
        #                         mode='w',
        #                         header=las_file.header,
        #                         do_compress=do_compress,
        #                         closefd=False,
        #                         laz_backends=olaz_backend) as las_out:
        #             las_out.vlrs = las_file.vlrs
        #             for points in las_file.chunk_iterator(1_216_418):
        #                 las_out.write(points)
        #                 # break
        #
        #     output.seek(0, io.SEEK_END)
        #     print(f"output is {output.tell()}")
        #     output.seek(0, io.SEEK_SET)
        #
        #     with open("dump.laz", mode="wb") as dumpf:
        #         dumpf.write(output.getbuffer())
        #
        #     original_las = pylas.read(str(file_path), laz_blackends=ilaz_backend)
        #     written_las = pylas.read(output, laz_blackends=ilaz_backend)
        #
        #     assert original_las.points.dtype == written_las.points.dtype
        #     for dim_name in original_las.points.dtype.names:
        #         assert np.allclose(original_las.points[dim_name],
        #                            written_las.points[dim_name]), f"{dim_name} dimensions are not equal"


        original_las = pylas.read(str(file_path), laz_blackends=ilaz_backend)
        with io.BytesIO() as output:
        # with open('lol.laz', mode="w+b") as output:
            original_las.write(output, do_compress=True, laz_backend=olaz_backend)

            print(output.tell())
            print(output.seek(0, io.SEEK_SET))

            original_las = pylas.read(str(file_path), laz_blackends=ilaz_backend)
            written_las = pylas.read(output, laz_blackends=ilaz_backend)

            assert original_las.points.dtype == written_las.points.dtype
            for dim_name in original_las.points.dtype.names:
                assert np.allclose(original_las.points[dim_name],
                                   written_las.points[dim_name]), f"{dim_name} dimensions are not equal"

        break


if __name__ == '__main__':
    main()
