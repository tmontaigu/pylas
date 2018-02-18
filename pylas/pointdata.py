import numpy as np

from .compression import decompress_stream
from .pointdimensions import get_dtype_of_format_id


class NumpyPointData:
    def __init__(self, data):
        self.data = data

    def __getitem__(self, item):
        return self.data[item]

    def __setitem__(self, key, value):
        self.data[key] = value

    def __len__(self):
        return self.data.shape[0]

    def write_to(self, out):
        raw_bytes = self.data.tobytes()
        out.write(raw_bytes)

    @classmethod
    def from_stream(cls, stream, point_format_id, count):
        points_dtype = get_dtype_of_format_id(point_format_id)

        point_data_buffer = stream.read(count * points_dtype.itemsize)
        data = np.frombuffer(point_data_buffer, dtype=points_dtype, count=count)
        data.flags.writeable = True
        return cls(data)

    @classmethod
    def from_compressed_stream(cls, compressed_stream, point_format_id, count, laszip_vlr):
        uncompressed = decompress_stream(compressed_stream, point_format_id, count, laszip_vlr)
        uncompressed.flags.writeable = True
        return cls(uncompressed)


def bitpack(arrs, indices):
    """Pack an array of integers into a byte based on idx
    for example bitpack((arr1, arr2), (0,3), (3,8)) packs the integers
    arr1 and arr2 into a byte, using the first three bits
    of arr1, and the last five bits of arr2.
    """

    def keep_bits(arr, low, high):
        """ Keep only the bits on the interval [low, high) """
        return np.bitwise_and(np.bitwise_and(arr, 2 ** high - 1),
                              ~(2 ** low - 1)).astype(np.uint8)

    first_bit_idx = 0  # Stack the bits from the beginning

    packed = np.zeros_like(arrs[0])
    for arr, (low, high) in zip(arrs, indices):
        if low > first_bit_idx:
            packed += np.right_shift(keep_bits(arr, low, high),
                                     low - first_bit_idx)
        else:
            packed += np.left_shift(keep_bits(arr, low, high),
                                    first_bit_idx - low)

        # First bit index should never be > 8 if we are
        # packing values to a byte
        first_bit_idx += high - low

        if first_bit_idx > 8:
            raise ValueError("Invalid Data: Packed Length is Greater than allowed.")

    return list(packed)
