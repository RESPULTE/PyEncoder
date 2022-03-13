from typing import List, TypeVar, NewType


ValidDataType = TypeVar("ValidDataType", str, int, float)
ValidDataset = TypeVar("ValidDataset", str, List[int], List[float])
Bitcode = NewType("BitCode", str)


class DecodingError(Exception):
    pass


class EncodingError(Exception):
    pass


class CorruptedHeaderError(Exception):
    pass


class CorruptedDataError(Exception):
    pass
