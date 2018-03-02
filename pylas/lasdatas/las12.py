from .base import LasBase


class LasData(LasBase):
    def __init__(self, *, header=None, vlrs=None, points=None):
        super().__init__(header=header, vlrs=vlrs, points=points)
