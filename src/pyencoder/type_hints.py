from typing import List, NewType, Union, Literal, Type, TypeVar

ValidData = Union[str, int, float]
ValidDataset = Union[str, List[int], List[float]]
Bitcode = NewType("BitCode", str)

SupportedDataType = Union[
    Type[Union[int, str, float]], Literal["b", "B", "h", "H", "i", "I", "l", "L", "q", "Q", "f", "d", "s"]
]

T = TypeVar("T")


class DecodingError(Exception):
    pass


class EncodingError(Exception):
    pass


class CorruptedHeaderError(Exception):
    pass


class CorruptedEncodingError(Exception):
    pass
