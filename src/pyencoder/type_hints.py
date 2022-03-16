from typing import List, Literal, TypeVar, NewType

from pyencoder.config import SUPPORTED_DTYPE_CODEBOOK

ValidDataType = TypeVar("ValidDataType", str, int, float)
ValidDataset = TypeVar("ValidDataset", str, List[int], List[float])
Bitcode = NewType("BitCode", str)

SupportedDataType = Literal[tuple([dtype.name for dtype in SUPPORTED_DTYPE_CODEBOOK])]  # type: ignore


class DecodingError(Exception):
    pass


class EncodingError(Exception):
    pass


class CorruptedHeaderError(Exception):
    pass


class CorruptedDataError(Exception):
    pass
