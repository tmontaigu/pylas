""" All the custom exceptions types
"""


class UnknownExtraType(Exception):
    pass


class PointFormatNotSupported(Exception):
    pass


class FileVersionNotSupported(Exception):
    pass


class LazPerfNotFound(Exception):
    pass


class IncompatibleDataFormat(Exception):
    pass

class LasVersionWarning(UserWarning):
    """
    Warnings related to incompatible values for LAS version.
    """