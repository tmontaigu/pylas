import logging
import pathlib
from typing import Union, Optional, Tuple, List

import numpy as np

from pylas import errors
from pylas.compression import LazBackend
from pylas.header import LasHeader
from pylas.laswriter import LasWriter
from pylas.point import record, dims, ExtraBytesParams, PointFormat
from pylas.point.dims import ScaledArrayView

logger = logging.getLogger(__name__)


class LasData:
    """Class synchronizing all the moving parts of LAS files.

    It connects the point record, header, vlrs together.

    To access points dimensions using this class you have two possibilities

    .. code:: python

        las = pylas.read('some_file.las')
        las.classification
        # or
        las['classification']
    """

    def __init__(
        self, header: LasHeader, points: Optional[record.PackedPointRecord] = None
    ):
        if points is None:
            points = record.PackedPointRecord.zeros(
                header.point_format, header.point_count
            )
        elif points.point_format != header.point_format:
            raise errors.PylasError("Incompatible Point Formats")
        self.__dict__["_points"] = points
        self.points: record.PackedPointRecord
        self.header: LasHeader = header
        if header.version.minor >= 4:
            self.evlrs: Optional[List] = []
        else:
            self.evlrs: Optional[List] = None

    @property
    def x(self):
        """Returns the scaled x positions of the points as doubles"""
        return ScaledArrayView(self.X, self.header.x_scale, self.header.x_offset)

    @x.setter
    def x(self, value):
        if len(value) > len(self.points):
            self.points.resize(len(value))
        self.x[:] = value

    @property
    def y(self):
        """Returns the scaled y positions of the points as doubles"""
        return ScaledArrayView(self.Y, self.header.y_scale, self.header.y_offset)

    @y.setter
    def y(self, value):
        if len(value) > len(self.points):
            self.points.resize(len(value))
        self.y[:] = value

    @property
    def z(self):
        """Returns the scaled z positions of the points as doubles"""
        return ScaledArrayView(self.Z, self.header.z_scale, self.header.z_offset)

    @z.setter
    def z(self, value):
        if len(value) > len(self.points):
            self.points.resize(len(value))
        self.z[:] = value

    @property
    def point_format(self) -> PointFormat:
        return self.points.point_format

    @property
    def points(self):
        return self._points

    @points.setter
    def points(self, new_points):
        if new_points.point_format != self._points.point_format:
            raise errors.IncompatibleDataFormat(
                "Cannot set points with a different point format, convert first"
            )
        self._points = new_points
        self.update_header()

    @property
    def vlrs(self):
        return self.header.vlrs

    def change_scaling(self, scales=None, offsets=None) -> None:
        if scales is None:
            scales = self.header.scales
        if offsets is None:
            offsets = self.header.offsets

        record.apply_new_scaling(self, scales, offsets)

        self.header.scales = scales
        self.header.offsets = offsets

    def __getattr__(self, item):
        """Automatically called by Python when the attribute
        named 'item' is no found. We use this function to forward the call the
        point record. This is the mechanism used to allow the users to access
        the points dimensions directly through a LasData.

        Parameters
        ----------
        item: str
            name of the attribute, should be a dimension name

        Returns
        -------
        The requested dimension if it exists

        """
        try:
            return self.points[item]
        except ValueError:
            raise AttributeError(
                f"{self.__class__.__name__} object has no attribute '{item}'"
            ) from None

    def __setattr__(self, key, value):
        """This is called on every access to an attribute of the instance.
        Again we use this to forward the call the the points record

        But this time checking if the key is actually a dimension name
        so that an error is raised if the user tries to set a valid
        LAS dimension even if it is not present in the field.
        eg: user tries to set the red field of a file with point format 0:
        an error is raised

        """
        if key in self.point_format.dimension_names:
            self.points[key] = value
        elif key in dims.DIMENSIONS_TO_TYPE:
            raise ValueError(
                f"Point format {self.point_format} does not support {key} dimension"
            )
        else:
            super().__setattr__(key, value)

    def __getitem__(self, item):
        return self.points[item]

    def __setitem__(self, key, value):
        self.points[key] = value

    def add_extra_dim(self, params: ExtraBytesParams):
        """Adds a new extra dimension to the point record

        .. note::

            If you plan on adding multiple extra dimensions,
            prefer :meth:`pylas.LasBase.add_extra_dims` as it will
            save re-allocations and data copy

        Parameters
        ----------
        name: str
            the name of the dimension, spaces are replaced with '_'.
        type: str
            type of the dimension (eg 'uint8' or 'u1')
        description: str, optional
            a small description of the dimension
        """
        self.add_extra_dims([params])

    def add_extra_dims(self, params: List[ExtraBytesParams]):
        """Add multiple extra dimensions at once

        Parameters
        ----------

        type_tuples:
               a list of tuple describing the dimensions to add
               [(name, type, description), (name2, other_type)]
               The description is optional
        """
        self.header.add_extra_dims(params)
        new_point_record = record.PackedPointRecord.from_point_record(
            self.points, self.header.point_format
        )
        self.points = new_point_record

    def update_header(self):
        """Update the information stored in the header
        to be in sync with the actual data.

        This method is called automatically when you save a file using
        :meth:`pylas.lasdatas.base.LasBase.write`
        """
        self.header.point_format_id = self.points.point_format.id
        self.header.point_count = len(self.points)
        self.header.point_data_record_length = self.points.point_size

        if len(self.points) > 0:
            self.header.x_max = self.x.max()
            self.header.y_max = self.y.max()
            self.header.z_max = self.z.max()

            self.header.x_min = self.x.min()
            self.header.y_min = self.y.min()
            self.header.z_min = self.z.min()

            unique, counts = np.unique(self.return_number, return_counts=True)
            self.header.number_of_points_by_return = counts

        if self.header.version.minor >= 4:
            if self.evlrs is not None:
                self.header.number_of_evlrs = len(self.evlrs)
            self.header.start_of_waveform_data_packet_record = 0
            # TODO
            # if len(self.vlrs.get("WktCoordinateSystemVlr")) == 1:
            #     self.header.global_encoding.wkt = 1
        else:
            self.header.number_of_evlrs = 0

    def write_to(
        self, out_stream, do_compress=False, laz_backend=LazBackend.detect_available()
    ):
        """writes the data to a stream

        Parameters
        ----------
        out_stream: file object
            the destination stream, implementing the write method
        do_compress: bool, optional, default False
            Flag to indicate if you want the data to be compressed
        laz_backend: optional, the laz backend to use
            By default, pylas detect available backends
        """
        with LasWriter(
            out_stream,
            self.header,
            do_compress=do_compress,
            closefd=False,
            laz_backend=laz_backend,
        ) as writer:
            writer.write(self.points)
            if self.header.version.minor >= 4 and self.evlrs is not None:
                writer.write_evlrs(self.evlrs)

    @staticmethod
    def _raise_if_not_expected_pos(stream, expected_pos):
        if not stream.tell() == expected_pos:
            raise RuntimeError(
                "Writing, expected to be at pos {} but stream is at pos {}".format(
                    expected_pos, stream.tell()
                )
            )

    def write_to_file(
        self, filename: Union[str, pathlib.Path], do_compress: Optional[bool] = None
    ) -> None:
        """Writes the las data into a file

        Parameters
        ----------
        filename : str
            The file where the data should be written.
        do_compress: bool, optional, default None
            if None the extension of the filename will be used
            to determine if the data should be compressed
            otherwise the do_compress flag indicate if the data should be compressed
        """
        is_ext_laz = pathlib.Path(filename).suffix.lower() == ".laz"
        if is_ext_laz and do_compress is None:
            do_compress = True

        with open(filename, mode="wb+") as out:
            self.write_to(out, do_compress=do_compress)

    def write(
        self, destination, do_compress=None, laz_backend=LazBackend.detect_available()
    ):
        """Writes to a stream or file

        When destination is a string, it will be interpreted as the path were the file should be written to,
        also if do_compress is None, the compression will be guessed from the file extension:

        - .laz -> compressed
        - .las -> uncompressed

        .. note::

            This means that you could do something like:
                # Create .laz but not compressed

                las.write('out.laz', do_compress=False)

                # Create .las but compressed

                las.write('out.las', do_compress=True)

            While it should not confuse Las/Laz readers, it will confuse humans so avoid doing it


        Parameters
        ----------
        destination: str or file object
            filename or stream to write to
        do_compress: bool, optional
            Flags to indicate if you want to compress the data
        laz_backend: optional, the laz backend to use
            By default, pylas detect available backends
        """
        if isinstance(destination, (str, pathlib.Path)):
            self.write_to_file(destination)
        else:
            if do_compress is None:
                do_compress = False
            self.write_to(destination, do_compress=do_compress, laz_backend=laz_backend)

    def __repr__(self):
        return "<LasData({}.{}, point fmt: {}, {} points, {} vlrs)>".format(
            self.header.version.major,
            self.header.version.minor,
            self.points.point_format,
            len(self.points),
            len(self.vlrs),
        )
