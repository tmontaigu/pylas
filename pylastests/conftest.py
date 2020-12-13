from pathlib import Path

import pytest
import pylas

SIMPLE_LAS_FILE_PATH = Path(__file__).parent / "simple.las"
VEGETATION1_3_LAS_FILE_PATH = Path(__file__).parent / "vegetation_1_3.las"
TEST1_4_LAS_FILE_PATH = Path(__file__).parent / "test1_4.las"
EXTRA_BYTES_LAS_FILE_PATH = Path(__file__).parent / "extrabytes.las"

SIMPLE_LAZ_FILE_PATH = Path(__file__).parent / "simple.laz"
EXTRA_BYTES_LAZ_FILE_PATH = Path(__file__).parent / "extra.laz"
PLANE_LAZ_FILE_PATH = Path(__file__).parent / "plane.laz"

ALL_LAS_FILE_PATH = [SIMPLE_LAS_FILE_PATH, VEGETATION1_3_LAS_FILE_PATH, TEST1_4_LAS_FILE_PATH,
                     EXTRA_BYTES_LAS_FILE_PATH]

ALL_LAZ_FILE_PATH = [
    SIMPLE_LAZ_FILE_PATH, EXTRA_BYTES_LAZ_FILE_PATH, PLANE_LAZ_FILE_PATH
]

ALL_LAZ_BACKEND = pylas.LazBackend.detect_available()


SUPPORTED_SINGULAR_EXTRA_BYTES_TYPE = ['u1', 'u2', 'u4', 'u8', 'i1', 'i2', 'i4', 'i8', 'f4', 'f8', 'uint8', 'uint16',
                                       'uint32',
                                       'uint64', 'int8',
                                       'int16', 'int32', 'int64', 'float32', 'float64']

SUPPORTED_ARRAY_2_EXTRA_BYTES_TYPE = [f'2{base_type}' for base_type in SUPPORTED_SINGULAR_EXTRA_BYTES_TYPE]

SUPPORTED_ARRAY_3_EXTRA_BYTES_TYPE = [f'3{base_type}' for base_type in SUPPORTED_SINGULAR_EXTRA_BYTES_TYPE]

SUPPORTED_EXTRA_BYTES_TYPE = SUPPORTED_SINGULAR_EXTRA_BYTES_TYPE + SUPPORTED_ARRAY_2_EXTRA_BYTES_TYPE + SUPPORTED_ARRAY_3_EXTRA_BYTES_TYPE


@pytest.fixture()
def simple_las_path():
    return SIMPLE_LAS_FILE_PATH


@pytest.fixture(params=SUPPORTED_EXTRA_BYTES_TYPE)
def extra_bytes_params(request):
    return pylas.ExtraBytesParams(
        name="just_a_name",
        type_str=request.param,
        description="pylas test ExtraBytes"
    )


@pytest.fixture(params=[EXTRA_BYTES_LAS_FILE_PATH, EXTRA_BYTES_LAZ_FILE_PATH], ids=repr)
def las_file_path_with_extra_bytes(request):
    if request.param.suffix == '.laz' and len(pylas.LazBackend.detect_available()) == 0:
        return pytest.skip("No Laz Backend")
    else:
        return request.param


@pytest.fixture(params=ALL_LAS_FILE_PATH, ids=repr)
def las_file_path(request):
    return request.param


@pytest.fixture(params=ALL_LAZ_FILE_PATH, ids=repr)
def laz_file_path(request):
    if len(pylas.LazBackend.detect_available()) == 0:
        return pytest.skip('No Laz Backend')
    return request.param


@pytest.fixture(params=ALL_LAS_FILE_PATH + ALL_LAZ_FILE_PATH, ids=repr)
def file_path(request):
    if len(pylas.LazBackend.detect_available()) == 0:
        return pytest.skip('No Laz Backend')
    return request.param


@pytest.fixture(params=ALL_LAZ_BACKEND if ALL_LAZ_BACKEND else [pytest.mark.skip("No Laz Backend installed")])
def laz_backend(request):
    return request.param


def all_las_file_path():
    return all_las_file_path()
