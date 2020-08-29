import threading


def ctypes_max_limit(byte_size, signed=False):
    nb_bits = (byte_size * 8) - (1 if signed else 0)
    return (2 ** nb_bits) - 1


def files_have_same_point_format_id(las_files):
    """Returns true if all the files have the same points format id"""
    point_format_found = {las.header.point_format_id for las in las_files}
    return len(point_format_found) == 1


def files_have_same_dtype(las_files):
    """Returns true if all the files have the same numpy datatype"""
    dtypes = {las.points.dtype for las in las_files}
    return len(dtypes) == 1


class ConveyorThread(threading.Thread):
    """class to be used as a separate thread by calling start()

    This class convey data from the input stream into the output stream.
    This is used when piping data into laszip.exe using python's subprocess.Popen
    when both of the stdin & stdout are in memory io objects because in such cases
    there is a deadlock occuring because we fill up the os stdout/stdin buffer

    So we need a separate thread to convey / move data from one source into another
    so that the main thread can read and we avoid deadlocks
    """

    def __init__(self, input_stream, output_stream, close_output=False):
        super().__init__()
        self.input_stream = input_stream
        self.output_stream = output_stream
        self.close_output = close_output
        self.should_end = False

    def run(self) -> None:
        for data in self.input_stream:
            if data:
                self.output_stream.write(data)
            elif self.should_end:
                break
            else:
                break

        if self.close_output:
            self.output_stream.close()

    def ask_for_termination(self) -> None:
        self.should_end = True
