def ctypes_max_limit(byte_size, signed=False):
    nb_bits = (byte_size * 8) - (1 if signed else 0)
    return (2 ** nb_bits) - 1
