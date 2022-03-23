from typing import List, NewType, Union, Literal

ValidDataType = Union[str, int, float]
ValidDataset = Union[str, List[int], List[float]]
Bitcode = NewType("BitCode", str)

SupportedDataType = Literal["b", "B", "h", "H", "i", "I", "l", "L", "q", "Q", "f", "d", "s"]


class DecodingError(Exception):
    pass


class EncodingError(Exception):
    pass


class CorruptedHeaderError(Exception):
    pass


class CorruptedEncodingError(Exception):
    pass
