def check_vlrs(las):
    if len(las.vlrs.get("GeoKeyDirectoryVlr")) > 1:
        raise ValueError("More than one GeoKeyDirectoryVlr")
    if len(las.vlrs.get("WktCoordinateSystemVlr")) > 1:
        raise ValueError("More than one WKT vlr")
