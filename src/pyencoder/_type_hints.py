from typing import Dict, Type, List, TypeVar, NewType
from collections.abc import Iterable


ValidDataType = TypeVar("ValidDataType", str, int, float)
ValidDataset = TypeVar("ValidDataset", str, list, tuple)
BitCode = NewType("BitCode", str)

SUPPORTED_DTYPE: Dict[bytes, Type] = {b"0": str, b"1": int, b"2": float}

DIV = b"\$"


class DecompressionError(Exception):
    pass


def _check_datatype(dataset: ValidDataType, dtype: Type):
    if not isinstance(dataset, Iterable):
        raise TypeError("dataset must be a non-empty iterable object")

    if dtype not in SUPPORTED_DTYPE.values():
        raise TypeError(f" datatype not supported '{dtype}'")


def _get_dtype_byte_header(dtype: ValidDataType):
    return list(SUPPORTED_DTYPE.keys())[list(SUPPORTED_DTYPE.values()).index(dtype)]
