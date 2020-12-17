import pylas


def test_mmap(mmapped_file_path):
    pylas.mmap(mmapped_file_path)
