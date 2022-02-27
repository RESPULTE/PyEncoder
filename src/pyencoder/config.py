from enum import auto, Enum

DEFAULT_DELIMITER = 69420
DEFAULT_MARKER = 42069
BYTEORDER = "little"

STRING_ENCODING = "utf-8"


class SUPPORTED_DTYPE(Enum):
    string = auto()
    int8 = auto()
    int32 = auto()
    int64 = auto()
    float64 = auto()
