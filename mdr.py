import pylas


header = pylas.LasHeader(point_format=pylas.PointFormat(6))
las = pylas.LasData(header)
las.write('mdr.las')
