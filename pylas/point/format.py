from itertools import zip_longest
from typing import Tuple, Optional, Iterable

import numpy as np

from . import dims
from .dims import DimensionInfo


class PointFormat:
    """Class that contains the dimensions that forms a PointFormat

    A PointFormat has 'standard' dimensions (dimensions defined in the LAS standard, each
    point format has its set of dimensions), but it can also have extra (non-standard) dimensions
    defined by the user)

    This class can be used to get information about dimensions of a point format.


    >>> fmt = PointFormat(3)
    >>> all(dim.is_standard for dim in fmt.dimensions)
    True
    >>> dim = fmt.dimension_by_name("classification") # or fmt["classification"]
    >>> dim.max
    31
    >>> dim.min
    0
    >>> dim.num_bits
    5

    """

    def __init__(
        self,
        point_format_id: int,
        extra_dims: Optional[Tuple[Tuple[str, str], ...]] = None,
    ):
        """
        Parameters
        ----------
        point_format_id: int
            point format id
        extra_dims: list of tuple
            [(name, type_str), ..] of extra dimensions attached to this point format
        """
        self.id = point_format_id
        self.dimensions = []
        composed_dims = dims.COMPOSED_FIELDS[self.id]
        for dim_name in dims.ALL_POINT_FORMATS_DIMENSIONS[self.id]:
            try:
                sub_fields = composed_dims[dim_name]
            except KeyError:
                dimension = DimensionInfo.from_type_str(
                    dim_name, dims.DIMENSIONS_TO_TYPE[dim_name], is_standard=True
                )
                self.dimensions.append(dimension)
            else:
                for sub_field in sub_fields:
                    dimension = DimensionInfo.from_bitmask(
                        sub_field.name, sub_field.mask, is_standard=True
                    )
                    self.dimensions.append(dimension)

        if extra_dims is not None:
            for name, type_str in extra_dims:
                self.add_extra_dimension(name, type_str)

    @property
    def standard_dimensions(self) -> Iterable[DimensionInfo]:
        return (dim for dim in self.dimensions if dim.is_standard)

    @property
    def extra_dimensions(self) -> Iterable[DimensionInfo]:
        return (dim for dim in self.dimensions if dim.is_standard is False)

    @property
    def dimension_names(self) -> Iterable[str]:
        """Returns the names of the dimensions contained in the point format"""
        return (dim.name for dim in self.dimensions)

    @property
    def standard_dimension_names(self) -> Iterable[str]:
        """Returns the names of the extra dimensions in this point format"""
        return (dim.name for dim in self.standard_dimensions)

    @property
    def extra_dimension_names(self) -> Iterable[str]:
        """Returns the names of the extra dimensions in this point format"""
        return (dim.name for dim in self.extra_dimensions)

    @property
    def size(self) -> int:
        """Returns the number of bytes (standard + extra)"""
        return int(sum(dim.num_bits for dim in self.dimensions) // 8)

    @property
    def num_standard_bytes(self) -> int:
        """Returns the number of bytes used by standard dims"""
        return int(sum(dim.num_bits for dim in self.standard_dimensions) // 8)

    @property
    def num_extra_bytes(self) -> int:
        """Returns the number of extra bytes"""
        return int(sum(dim.num_bits for dim in self.extra_dimensions) // 8)

    @property
    def has_waveform_packet(self):
        """Returns True if the point format has waveform packet dimensions"""
        dimensions = set(self.dimension_names)
        return all(name in dimensions for name in dims.WAVEFORM_FIELDS_NAMES)

    def dimension_by_name(self, name: str) -> DimensionInfo:
        for dim in self.dimensions:
            if dim.name == name:
                return dim
        raise ValueError(f"Dimension '{name}' does not exist")

    def add_extra_dimension(self, name: str, type_str: str) -> None:
        self.dimensions.append(
            DimensionInfo.from_type_str(name, type_str, is_standard=False)
        )

    def dtype(self):
        """Returns the numpy.dtype used to store the point records in a numpy array

        .. note::

            The dtype corresponds to the dtype with sub_fields *packed* into their
            composed fields

        """
        dtype = dims.ALL_POINT_FORMATS_DTYPE[self.id]
        descr = dtype.descr
        for extra_dim in self.extra_dimensions:
            descr.append((extra_dim.name, extra_dim.type_str()))
        return np.dtype(descr)

    def __getitem__(self, item):
        if isinstance(item, str):
            return self.dimension_by_name(item)
        return self.dimensions[item]

    def __eq__(self, other):
        if self.id != other.id:
            return False

        for my_eb, ot_eb in zip_longest(self.extra_dimensions, other.extra_dimensions):
            if my_eb != ot_eb:
                return False

        return True

    def __repr__(self):
        return "<PointFormat({}, {} bytes of extra dims)>".format(
            self.id, self.num_extra_bytes
        )


def lost_dimensions(point_fmt_in, point_fmt_out):
    """Returns a list of the names of the dimensions that will be lost
    when converting from point_fmt_in to point_fmt_out
    """

    dimensions_in = set(PointFormat(point_fmt_in).dimension_names)
    dimensions_out = set(PointFormat(point_fmt_out).dimension_names)

    completely_lost = []
    for dim_name in dimensions_in:
        if dim_name not in dimensions_out:
            completely_lost.append(dim_name)
    return completely_lost
