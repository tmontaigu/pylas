import pathlib
from typing import Union

from .compression import LazBackend
from .lasdatas import las12, las14

LazBackend = LazBackend

LasData = Union[las12.LasData, las14.LasData]

PathLike = Union[str, pathlib.Path]
