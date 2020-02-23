import io
import logging
import struct

from . import headers, errors, evlrs
from .compression import laszip_decompress, pylaz_decompress_buffer, lazperf_decompress_buffer
from .lasdatas import las14, las12
from .point import record, PointFormat
from .vlrs import rawvlr
from .vlrs.vlrlist import VLRList

logger = logging.getLogger(__name__)


def _raise_if_wrong_file_signature(stream):
    """ Reads the 4 first bytes of the stream to check that is LASF"""
    file_sig = stream.read(len(headers.LAS_FILE_SIGNATURE))
    if file_sig != headers.LAS_FILE_SIGNATURE:
        raise errors.PylasError(
            "File Signature ({}) is not {}".format(file_sig, headers.LAS_FILE_SIGNATURE)
        )


class LasReader:
    """ This class handles the reading of the different parts of a las file.

    As the Header is necessary to be able to understand how the data is structured,
    it will be read during initialisation of the instance

    """

    def __init__(self, stream, closefd=True):
        self.start_pos = stream.tell()
        _raise_if_wrong_file_signature(stream)
        self.stream = stream
        self.closefd = closefd
        self.header = self.read_header()

    def read_header(self):
        """ Reads the head of the las file and returns it
        """
        self.stream.seek(self.start_pos)
        return headers.HeaderFactory().read_from_stream(self.stream)

    def read_vlrs(self):
        """ Reads and return the vlrs of the file
        """
        self.stream.seek(self.start_pos + self.header.size)
        return VLRList.read_from(self.stream, num_to_read=self.header.number_of_vlr)

    def read(self):
        """ Reads the whole las data (header, vlrs ,points, etc) and returns a LasData
        object
        """
        vlrs = self.read_vlrs()
        self._warn_if_not_at_expected_pos(
            self.header.offset_to_point_data, "end of vlrs", "start of points"
        )
        self.stream.seek(self.start_pos + self.header.offset_to_point_data)

        try:
            points = self._read_points(vlrs)
        except (RuntimeError, errors.LazPerfNotFound) as e:
            logger.error("LazPerf failed to decompress ({}), trying laszip.".format(e))
            self.stream.seek(self.start_pos)
            self.__init__(io.BytesIO(laszip_decompress(self.stream)))
            return self.read()

        if points.point_format.has_waveform_packet:
            self.stream.seek(
                self.start_pos + self.header.start_of_waveform_data_packet_record
            )
            if self.header.global_encoding.are_waveform_flag_equal():
                raise errors.PylasError(
                    "Incoherent values for internal and external waveform flags, both are {})".format(
                        "set"
                        if self.header.global_encoding.waveform_internal
                        else "unset"
                    )
                )
            if self.header.global_encoding.waveform_internal:
                # TODO: Find out what to do with these
                _, _ = self._read_internal_waveform_packet()
            elif self.header.global_encoding.waveform_external:
                logger.info(
                    "Waveform data is in an external file, you'll have to load it yourself"
                )

        if self.header.version >= "1.4":
            evlrs = self.read_evlrs()
            return las14.LasData(
                header=self.header, vlrs=vlrs, points=points, evlrs=evlrs
            )

        return las12.LasData(header=self.header, vlrs=vlrs, points=points)

    def _read_points(self, vlrs):
        """ private function to handle reading of the points record parts
        of the las file.

        the header is needed for the point format and number of points
        the vlrs are need to get the potential laszip vlr as well as the extra bytes vlr
        """
        try:
            extra_dims = vlrs.get("ExtraBytesVlr")[0].type_of_extra_dims()
        except IndexError:
            extra_dims = None

        point_format = PointFormat(self.header.point_format_id, extra_dims=extra_dims)
        if self.header.are_points_compressed:
            laszip_vlr = vlrs.pop(vlrs.index("LasZipVlr"))
            points = self._read_compressed_points_data(laszip_vlr, point_format)
        else:
            points = record.PackedPointRecord.from_stream(
                self.stream, point_format, self.header.point_count
            )
        return points

    def _read_compressed_points_data(self, laszip_vlr, point_format):
        """ reads the compressed point record
        """
        if self.header.version >= "1.4" and self.header.number_of_evlr > 0:
            size_of_point_data = self.header.start_of_first_evlr - self.stream.tell()
        else:
            size_of_point_data = -1  # Read everything

        current_pos = self.stream.tell()
        points_data = bytearray(self.stream.read(size_of_point_data))
        offset_to_chunk_table = struct.unpack("<q", points_data[:8])[0]
        offset_to_chunk_table -= current_pos
        struct.pack_into("<q", points_data, 0, offset_to_chunk_table)

        try:
            decompressed_points = pylaz_decompress_buffer(
                points_data,
                point_format.dtype.itemsize,
                self.header.point_count,
                laszip_vlr
            )
        except errors.LazError as e:
            logger.error("pylaz failed to decompress points: {}".format(e))
            points_data = points_data[8:]

            decompressed_points = lazperf_decompress_buffer(
                points_data,
                point_format.dtype.itemsize,
                self.header.point_count,
                laszip_vlr
            )

        points = record.PackedPointRecord.from_buffer(
            decompressed_points,
            point_format,
            self.header.point_count
        )
        return points

    def _read_internal_waveform_packet(self):
        """ reads and returns the waveform vlr header, waveform record
        """
        # This is strange, the spec says, waveform data packet is in a EVLR
        #  but in the 2 samples I have its a VLR
        # but also the 2 samples have a wrong user_id (LAS_Spec instead of LASF_Spec)
        b = bytearray(self.stream.read(rawvlr.VLR_HEADER_SIZE))
        waveform_header = rawvlr.RawVLRHeader.from_buffer(b)
        waveform_record = self.stream.read()
        logger.debug(
            "Read: {} MBytes of waveform_record".format(len(waveform_record) / 10 ** 6)
        )

        return waveform_header, waveform_record

    def read_evlrs(self):
        """ Reads the EVLRs of the file, will fail if the file version
        does not support evlrs
        """
        self.stream.seek(self.start_pos + self.header.start_of_first_evlr)
        return evlrs.EVLRList.read_from(self.stream, self.header.number_of_evlr)

    def _warn_if_not_at_expected_pos(self, expected_pos, end_of, start_of):
        """ Helper function to warn about unknown bytes found in the file"""
        diff = expected_pos - self.stream.tell()
        if diff != 0:
            logger.warning(
                "There are {} bytes between {} and {}".format(diff, end_of, start_of)
            )

    def close(self):
        """ closes the file object used by the reader
        """
        self.stream.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.closefd:
            self.close()
