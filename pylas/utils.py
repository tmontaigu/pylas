def ctypes_max_limit(byte_size, signed=False):
    nb_bits = (byte_size * 8) - (1 if signed else 0)
    return (2 ** nb_bits) - 1


def files_have_same_point_format_id(las_files):
    """ Returns true if all the files have the same points format id
    """
    point_format_found = {las.header.point_format_id for las in las_files}
    return len(point_format_found) == 1


def files_have_same_dtype(las_files):
    """ Returns true if all the files have the same numpy datatype
    """
    dtypes = {las.points.dtype for las in las_files}
    return len(dtypes) == 1
