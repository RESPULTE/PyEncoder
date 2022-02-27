from typing import TypeVar, NewType


ValidDataType = TypeVar("ValidDataType", str, int, float)
ValidDataset = TypeVar("ValidDataset", str, list, tuple)
BinaryCode = NewType("BitCode", str)


class DecompressionError(Exception):
    pass
