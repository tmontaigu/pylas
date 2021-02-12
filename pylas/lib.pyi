from typing import Union, Iterable, BinaryIO, overload, Optional

from compression import LazBackend
from lasappender import LasAppender
from pylas import LasWriter, LasHeader, LasReader
from typehints import Literal, PathLike
@overload
def open_las(
    source: PathLike,
    mode: Literal["r"] = ...,
    laz_backend: Union[LazBackend, Iterable[LazBackend]] = ...,
) -> LasReader: ...
@overload
def open_las(
    source: BinaryIO,
    mode: Literal["r"] = ...,
    closefd: bool = ...,
    laz_backend: Union[LazBackend, Iterable[LazBackend]] = ...,
) -> LasReader: ...
@overload
def open_las(
    source: PathLike,
    mode: Literal["w"],
    header: LasHeader,
    do_compress: Optional[bool] = ...,
    laz_backend: Union[LazBackend, Iterable[LazBackend]] = ...,
) -> LasWriter: ...
@overload
def open_las(
    source: BinaryIO,
    mode: Literal["w"],
    header: LasHeader,
    do_compress: Optional[bool] = ...,
    closefd: bool = ...,
    laz_backend: Union[LazBackend, Iterable[LazBackend]] = ...,
) -> LasWriter: ...
@overload
def open_las(
    source: PathLike,
    mode: Literal["a"],
    laz_backend: Union[LazBackend, Iterable[LazBackend]] = ...,
) -> LasAppender: ...
@overload
def open_las(
    source: BinaryIO,
    mode: Literal["a"],
    closefd: bool = ...,
    laz_backend: Union[LazBackend, Iterable[LazBackend]] = ...,
) -> LasAppender: ...
def open_las(
    source,
    mode="r",
    closefd=True,
    laz_backend=None,
    header=None,
    do_compress=None,
): ...
