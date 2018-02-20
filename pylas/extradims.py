from . import errors

extra_dims_base = (
    '',  # 0 is 'undocumented extra bytes', not sure what to do with that
    'u1',
    'i1',
    'u2',
    'i2',
    'u4',
    'i4',
    'u8',
    'i8',
    'f4',
    'f8',
)

extra_dims_2 = tuple('2{}'.format(_type) for _type in extra_dims_base[1:])
extra_dims_3 = tuple('3{}'.format(_type) for _type in extra_dims_base[1:])

extra_dims = extra_dims_base + extra_dims_2 + extra_dims_3


def get_type_for_extra_dim(type_index):
    try:
        return extra_dims[type_index]
    except IndexError:
        raise errors.UnknownExtraType(type_index)
