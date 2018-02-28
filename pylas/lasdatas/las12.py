import numpy as np

from .base import LasBase
from .. import vlr, pointdims


class LasData(LasBase):
    def __init__(self, header=None, vlrs=None, points=None):
        super().__init__(header, vlrs, points)

