import threading


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


class ConveyorThread(threading.Thread):
    """ class to be used as a separate thread by calling start()

    This class convey data from the input stream into the output stream.
    This is used when piping data into laszip.exe using python's subprocess.Popen
    when both of the stdin & stdout are in memory io objects because in such cases
    there is a deadlock ocuring because we fill up the os stdout buffer

    So we need a thread to read data from the stdout using another thread
    to avoid deadlocking
    """
    def __init__(self, input_stream, output_stream):
        super().__init__()
        self.input_stream = input_stream
        self.output_stream = output_stream

    def run(self) -> None:
        for data in self.input_stream:
            if data:
                self.output_stream.write(data)
            else:
                break
