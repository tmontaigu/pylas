import numpy as np

from . import dims
from .. import errors


class PointFormat:
    """ Class that handles all the information about a point format

    Most of the methods/properties will throw a
    pylas.errors.PointFormatNotSupported if the point format id is not supported
    """

    def __init__(self, point_format_id, extra_dims=None):
        """
        Parameters
        ----------
        point_format_id: int
            point format id
        extra_dims: list of tuple
            [(name, type_str), ..] of extra dimensions attached to this point format
        """
        self.id = point_format_id
        if extra_dims is None:
            extra_dims = []
        self.extra_dims = extra_dims

    @property
    def dimension_names(self):
        """ Returns the names of the dimensions contained in the point format

        Returns
        -------
        list of str
            the names of the dimensions defined by this point format

        """
        return self.unpacked_dtype.names

    @property
    def size(self):
        return self.dtype.itemsize

    @property
    def dtype(self):
        """ Returns the numpy.dtype used to store the point records in a numpy array

        .. note::

            The dtype corresponds to the dtype with sub_fields *packed* into their
            composed fields

        """
        dtype = self._access_dict(dims.ALL_POINT_FORMATS_DTYPE, self.id)
        dtype = self._dtype_add_extra_dims(dtype)
        return dtype

    @property
    def unpacked_dtype(self):
        """ Returns the numpy.dtype used to store the point records in a numpy array

        .. note::

            The dtype corresponds to the dtype with sub_fields *unpacked*

        """
        dtype = self._access_dict(dims.UNPACKED_POINT_FORMATS_DTYPES, self.id)
        dtype = self._dtype_add_extra_dims(dtype)
        return dtype

    @property
    def composed_fields(self):
        """ Returns the dict of composed fields defined for the point format

        Returns
        -------
        Dict[str, List[SubFields]]
            maps a composed field name to its sub_fields

        """
        return self._access_dict(dims.COMPOSED_FIELDS, self.id)

    @property
    def sub_fields(self):
        """ Returns a dict of the sub fields for this point format

        Returns
        -------
        Dict[str, Tuple[str, SubField]]
            maps a sub field name to its composed dimension with additional information

        """
        sub_fields_dict = {}
        for composed_dim_name, sub_fields in self.composed_fields.items():
            for sub_field in sub_fields:
                sub_fields_dict[sub_field.name] = (composed_dim_name, sub_field)
        return sub_fields_dict

    @property
    def extra_dimension_names(self):
        """ Returns the list of extra dimensions attached to this point format
        """
        return [extd[0] for extd in self.extra_dims]

    @property
    def num_extra_bytes(self):
        """ Returns the number of extra bytes
        """
        return sum(np.dtype(extra_dim[1]).itemsize for extra_dim in self.extra_dims)

    @property
    def has_waveform_packet(self):
        """ Returns True if the point format has waveform packet dimensions
        """
        dimensions = set(self.dimension_names)
        return all(name in dimensions for name in dims.WAVEFORM_FIELDS_NAMES)

    def dimension_type_info(self, dimension_name):
        return np.iinfo(self.dtype[dimension_name])

    @staticmethod
    def _access_dict(d, key):
        try:
            return d[key]
        except KeyError as e:
            raise errors.PointFormatNotSupported(e)

    def _dtype_add_extra_dims(self, dtype):
        if self.extra_dims:
            descr = dtype.descr
            descr.extend(self.extra_dims)
            dtype = np.dtype(descr)
        return dtype

    def __eq__(self, other):
        if self.id != other.id:
            return False

        if self.extra_dims != other.extra_dims:
            return False

        return True

    def __int__(self):
        return self.id

    def __repr__(self):
        return "<PointFormat({})>".format(self.id)

    def is_supported(self):
        return self.id in dims.ALL_POINT_FORMATS_DIMENSIONS


def lost_dimensions(point_fmt_in, point_fmt_out):
    """  Returns a list of the names of the dimensions that will be lost
    when converting from point_fmt_in to point_fmt_out
    """

    unpacked_dims_in = PointFormat(point_fmt_in).dtype
    unpacked_dims_out = PointFormat(point_fmt_out).dtype

    out_dims = unpacked_dims_out.fields
    completely_lost = []
    for dim_name in unpacked_dims_in.names:
        if dim_name not in out_dims:
            completely_lost.append(dim_name)
    return completely_lost
