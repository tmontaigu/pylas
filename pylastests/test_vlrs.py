import io

import pytest

import pylas
from pylas.evlrs import RawEVLR, EVLR_HEADER_SIZE, EVLRList, EVLR, RawEVLRList
from pylas.vlrs import VLR_HEADER_SIZE
from pylastests import test_common


def test_adding_classification_lookup():
    simple = pylas.read(test_common.simple_las)
    classification_lookup = pylas.vlrs.known.ClassificationLookupVlr()

    assert len(classification_lookup.lookups) == 0
    classification_lookup[20] = "computer"
    assert len(classification_lookup.lookups) == 1
    classification_lookup[17] = "car"

    simple.vlrs.append(classification_lookup)

    simple = test_common.write_then_read_again(simple)
    classification_lookups = simple.vlrs.get("ClassificationLookupVlr")[0]

    assert classification_lookups[20] == "computer"
    assert classification_lookups[17] == "car"


def test_lookup_out_of_range():
    classification_lookup = pylas.vlrs.known.ClassificationLookupVlr()
    with pytest.raises(ValueError):
        classification_lookup[541] = "LiquidWater"

    with pytest.raises(ValueError):
        classification_lookup[-42] = "SolidWater"


def test_adding_extra_bytes_vlr_by_hand():
    """
    Test that if someone adds an ExtraBytesVlr by himself
    without having matching extra bytes in the point record, the
    ExtraByteVlr is removed before writing
    """

    simple = pylas.read(test_common.simple_las)
    ebvlr = pylas.vlrs.known.ExtraBytesVlr()
    ebs = pylas.vlrs.known.ExtraBytesStruct(data_type=3, name="Fake".encode())
    ebvlr.extra_bytes_structs.append(ebs)
    simple.vlrs.append(ebvlr)
    assert len(simple.vlrs.get("ExtraBytesVlr")) == 1

    las = pylas.lib.write_then_read_again(simple)
    assert simple.points.point_size == las.points.point_size
    assert len(las.vlrs.get("ExtraBytesVlr")) == 0


def test_raw_evlr_read_write():
    raw_evlr = RawEVLR()
    raw_evlr.header.user_id = b"Ascalon"
    raw_evlr.header.record_id = 17

    assert raw_evlr.size_in_bytes() == EVLR_HEADER_SIZE

    with io.BytesIO() as o:
        raw_evlr.write_to(o)
        o.seek(0)

        assert len(o.getvalue()) == EVLR_HEADER_SIZE

        r = RawEVLR.read_from(o)
    assert raw_evlr == r


def test_evlr():
    evlr = EVLR(user_id="pylastest", record_id=42, description="Just a test")
    evlr.record_data = b"While he grinds his own hands"

    evlrs = EVLRList()
    evlrs.append(evlr)

    raws_evlrs = RawEVLRList.from_list(evlrs)
    assert len(raws_evlrs) == 1

    raw = next(iter(raws_evlrs))
    assert raw.header.user_id == b"pylastest"
    assert raw.header.record_id == 42
    assert raw.header.description == b"Just a test"
    assert raw.header.record_length_after_header == len(evlr.record_data)
    assert raw.record_data == evlr.record_data

    with io.BytesIO() as o:
        raws_evlrs.write_to(o)

        assert len(o.getvalue()) == raw.size_in_bytes()
