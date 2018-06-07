import pylas
from pylastests import test_common


def test_adding_classification_lookup():
    simple = pylas.read(test_common.simple_las)
    classification_lookup = pylas.vlrs.known.ClassificationLookupVlr()

    assert len(classification_lookup.lookups) == 0
    classification_lookup.add_lookup(20, "computer")
    assert len(classification_lookup.lookups) == 1
    classification_lookup.add_lookup(17, "car")

    simple.vlrs.append(classification_lookup)

    simple = test_common.write_then_read_again(simple)
    classification_lookups = simple.vlrs.get("ClassificationLookupVlr")
    assert len(classification_lookups) == 1

    classification_lookup = classification_lookups[0]
    lookups = {
        lookup.class_number: lookup.description
        for lookup in classification_lookup.lookups
    }

    assert lookups[20] == "computer"
    assert lookups[17] == "car"
