__version__ = "0.5.0a1"

import logging

from . import errors, vlrs
from .evlrs import EVLR
from .headers import HeaderFactory
from .laswriter import LasWriter
from .errors import PylasError
from .lib import LazBackend
from .lib import convert, create_from_header
from .lib import create_las as create
from .lib import merge_las as merge
from .lib import mmap_las as mmap
from .lib import open_las as open
from .lib import read_las as read
from .point import PointFormat, DimensionKind, DimensionInfo
from .point.dims import supported_point_formats, supported_versions
from .point.format import lost_dimensions

logging.getLogger(__name__).addHandler(logging.NullHandler())
