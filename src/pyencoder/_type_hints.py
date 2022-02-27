from typing import TypeVar, NewType


ValidDataType = TypeVar("ValidDataType", str, int, float)
ValidDataset = TypeVar("ValidDataset", str, list, tuple)
BitCode = NewType("BitCode", str)


class DecompressionError(Exception):
    pass
