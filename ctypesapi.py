import ctypes

from ctypes import pythonapi

PyBUF_SIMPLE = 0
PyBUF_WRITABLE = 1


class Py_buffer(ctypes.Structure):
    _fields_ = [
        ('buf', ctypes.c_void_p),
        ('obj', ctypes.py_object),
        ('len', ctypes.c_ssize_t),
        ('itemsize', ctypes.c_ssize_t),
        ('readonly', ctypes.c_int),
        ('ndim', ctypes.c_int),
        ('format', ctypes.c_char_p),
        ('shape', ctypes.POINTER(ctypes.c_ssize_t)),
        ('strides', ctypes.POINTER(ctypes.c_ssize_t)),
        ('suboffsets', ctypes.POINTER(ctypes.c_ssize_t)),
        ('internal', ctypes.c_void_p)
    ]


ba = b"hello"


def print_buffer_info(b):
    buffer = Py_buffer()
    if pythonapi.PyObject_GetBuffer(ctypes.py_object(b), ctypes.byref(buffer), PyBUF_SIMPLE) != 0:
        raise SystemExit("can't get buffer")
    print("len of buffer is", buffer.len)
    print("itemsize is:", buffer.itemsize)
    print("format is:", buffer.format)
    print("ndim is:", buffer.ndim)
    print("is readonly:", buffer.readonly)
    print(bool(buffer.shape))
    # Release the buffer obj

print_buffer_info(ba)
print_buffer_info(bytearray(b"lololol"))

