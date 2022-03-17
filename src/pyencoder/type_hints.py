from typing import List, NewType, Union

from pyencoder.config import SUPPORTED_DTYPE

ValidDataType = Union[str, int, float]
ValidDataset = Union[str, List[int], List[float]]
Bitcode = NewType("BitCode", str)

SupportedDataType = SUPPORTED_DTYPE


class DecodingError(Exception):
    pass


class EncodingError(Exception):
    pass


class CorruptedHeaderError(Exception):
    pass


class CorruptedEncodingError(Exception):
    pass
