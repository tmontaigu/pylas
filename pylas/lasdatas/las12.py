from .base import LasBase


class LasData(LasBase):
    def __init__(self, *, header=None, vlrs=None, points=None):
        super().__init__(header=header, vlrs=vlrs, points=points)

    def __repr__(self):
        return 'LasData(1.2, point fmt: {}, {} points, {} vlrs)'.format(
            self.points_data.point_format_id, len(self.points_data), len(self.vlrs)
        )
