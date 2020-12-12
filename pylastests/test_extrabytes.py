"""
Tests related to extra bytes
"""

import numpy as np
import pytest

import pylas
from pylas.lib import write_then_read_again


def test_read_example_extra_bytes_las(las_file_path_with_extra_bytes):
    """
    Test that we can read the files with extra bytes with have as examples
    """
    las = pylas.read(las_file_path_with_extra_bytes)
    expected_names = [
        "Colors",
        "Reserved",
        "Flags",
        "Intensity",
        "Time",
    ]
    assert expected_names == list(las.points.extra_dimensions_names)


def test_read_write_example_extra_bytes_file(las_file_path_with_extra_bytes):
    """
    Test that we can write extra bytes without problem
    """
    original = pylas.read(las_file_path_with_extra_bytes)
    las = write_then_read_again(original)

    for name in original.point_format.dimension_names:
        assert np.allclose(las[name], original[name])


def test_adding_extra_bytes_keeps_values_of_all_existing_fields(extra_bytes_params, simple_las_path):
    """
    Test that when extra bytes are added, the existing fields keep their
    values and then we don't somehow drop them
    """
    las = pylas.read(simple_las_path)
    las.add_extra_dim(extra_bytes_params)

    original = pylas.read(simple_las_path)

    for name in original.point_format.dimension_names:
        assert np.allclose(las[name], original[name])


def test_creating_extra_bytes(extra_bytes_params, simple_las_path):
    """
    Test that we can create extra byte dimensions for each
    data type. And they can be written then read.
    """
    las = pylas.read(simple_las_path)
    las.add_extra_dim(extra_bytes_params)

    assert np.allclose(las[extra_bytes_params.name], 0)

    las[extra_bytes_params.name][:] = 42
    assert np.allclose(las[extra_bytes_params.name], 42)

    las = write_then_read_again(las)
    assert np.allclose(las[extra_bytes_params.name], 42)


def test_creating_scaled_extra_bytes(extra_bytes_params, simple_las_path):
    las = pylas.read(simple_las_path)
    params = pylas.ExtraBytesParams(
        extra_bytes_params.name,
        extra_bytes_params.type_str,
        extra_bytes_params.type_str,
        offsets=np.array([2.0, 2.0, 2.0]),
        scales=np.array([1.0, 1.0, 1.0])
    )
    las.add_extra_dim(params)

    assert np.allclose(las[extra_bytes_params.name], 2.0)

    las[params.name][:] = 42.0
    assert np.allclose(las[extra_bytes_params.name], 42.0)

    las = write_then_read_again(las)
    assert np.allclose(las[extra_bytes_params.name], 42.0)


def test_extra_bytes_description_is_ok(extra_bytes_params, simple_las_path):
    """
    Test that the description in ok
    """
    las = pylas.read(simple_las_path)
    las.add_extra_dim(extra_bytes_params)

    extra_dim_info = list(las.point_format.extra_dimensions)
    assert len(extra_dim_info) == 1
    assert extra_dim_info[0].description == extra_bytes_params.description

    las = write_then_read_again(las)

    extra_dim_info = list(las.point_format.extra_dimensions)
    assert len(extra_dim_info) == 1
    assert extra_dim_info[0].description == extra_bytes_params.description


def test_extra_bytes_with_spaces_in_name(simple_las_path):
    """
    Test that we can create extra bytes with spaces in their name
    and that they can be accessed using __getitem__ ( [] )
    as de normal '.name' won't work
    """
    las = pylas.read(simple_las_path)
    las.add_extra_dim(
        pylas.ExtraBytesParams(name="Name With Spaces", type_str="int32"))

    assert np.alltrue(las["Name With Spaces"] == 0)
    las["Name With Spaces"][:] = 789_464

    las = write_then_read_again(las)
    np.alltrue(las["Name With Spaces"] == 789_464)


def test_conversion_keeps_eb(las_file_path_with_extra_bytes):
    """
    Test that converting point format does not lose extra bytes
    """
    original = pylas.read(las_file_path_with_extra_bytes)
    converted_las = pylas.convert(original, point_format_id=0)

    assert len(list(original.point_format.extra_dimension_names)) == 5
    assert (
            list(converted_las.point_format.extra_dimension_names)
            == list(original.point_format.extra_dimension_names)
    )
    for name in converted_las.points.extra_dimensions_names:
        assert np.allclose(converted_las[name], original[name])

    converted_las = pylas.lib.write_then_read_again(converted_las)
    assert (
            list(converted_las.point_format.extra_dimension_names)
            == list(original.point_format.extra_dimension_names)
    )
    for name in converted_las.point_format.extra_dimension_names:
        assert np.allclose(converted_las[name], original[name])


def test_creating_bytes_with_name_too_long(simple_las_path):
    """
    Test error thrown when creating extra bytes with a name that is too long
    """
    las = pylas.read(simple_las_path)
    with pytest.raises(ValueError) as error:
        las.add_extra_dim(
            pylas.ExtraBytesParams(
                name="Lorem ipsum dolor sit amet, consectetur adipiscing elit. Sed non risus",
                type_str="int32"))

    assert str(error.value) == "bytes too long (70, maximum length 32)"


def test_creating_bytes_with_description_too_long(simple_las_path):
    """
    Test error thrown when creating extra bytes with a name that is too long
    """
    las = pylas.read(simple_las_path)
    with pytest.raises(ValueError) as error:
        las.add_extra_dim(
            pylas.ExtraBytesParams(
                name="a fine name",
                type_str="int32",
                description="Lorem ipsum dolor sit amet, consectetur adipiscing elit."
                            " Sed non risus"))

    assert str(error.value) == "bytes too long (70, maximum length 32)"


def test_creating_extra_byte_with_invalid_type(simple_las_path):
    """
    Test the error message when creating extra bytes with invalid type
    """
    las = pylas.read(simple_las_path)
    with pytest.raises(TypeError) as error:
        las.add_extra_dim(pylas.ExtraBytesParams("just_a_test", 'i16'))
    assert str(error.value) == "data type 'i16' not understood"
