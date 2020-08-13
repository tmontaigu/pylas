__version__ = "0.4.2"

from . import errors, vlrs
from .headers import HeaderFactory
from .lib import convert, create_from_header
from .lib import create_las as create
from .lib import mmap_las as mmap
from .lib import open_las as open
from .lib import read_las as read
from .lib import merge_las as merge
from .lib import LazBackend
from .point import PointFormat
from .point.dims import supported_point_formats, supported_versions
from .point.format import lost_dimensions
from .evlrs import EVLR
from .laswriter import LasWriter

import logging
logging.getLogger(__name__).addHandler(logging.NullHandler())