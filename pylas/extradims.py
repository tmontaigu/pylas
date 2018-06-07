from . import errors

extra_dims_base = ("", "u1", "i1", "u2", "i2", "u4", "i4", "u8", "i8", "f4", "f8")

extra_dims_2 = tuple("2{}".format(_type) for _type in extra_dims_base[1:])
extra_dims_3 = tuple("3{}".format(_type) for _type in extra_dims_base[1:])
extra_dims = extra_dims_base + extra_dims_2 + extra_dims_3

type_to_extra_dim_id = {type_str: i for i, type_str in enumerate(extra_dims)}


def get_type_for_extra_dim(type_index):
    try:
        return extra_dims[type_index]
    except IndexError:
        raise errors.UnknownExtraType(type_index)


def get_id_for_extra_dim_type(type_str):
    try:
        return type_to_extra_dim_id[type_str]
    except KeyError:
        raise errors.UnknownExtraType(type_str)
