from .lasdata import LasData


def open(source):
    return LasData.open(source)
