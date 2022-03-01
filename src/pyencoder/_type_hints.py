from typing import List, TypeVar, NewType


ValidDataType = TypeVar("ValidDataType", str, int, float)
ValidDataset = TypeVar("ValidDataset", str, List[int], List[float])
BinaryCode = NewType("BitCode", str)


class DecompressionError(Exception):
    pass


class CompressionError(Exception):
    pass


class CorruptedHuffmanStringError(Exception):
    pass


class CorruptedHuffmanDataError(Exception):
    pass
