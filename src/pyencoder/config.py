from typing import Dict, Type

DEFAULT_DELIMITER = 69420
DEFAULT_HUFFMARKER = 42069
DEFAULT_DTYPEMARKER_SIZE = 2
BYTEORDER = "little"

STRING_ENCODING = "utf-8"

SUPPORTED_DTYPE_TO_BIN: Dict[Type, str] = {
    str: "01",
    int: "10",
    float: "11",
}

SUPPORTED_DTYPE_FROM_BIN: Dict[Type, str] = {"01": str, "10": int, "11": float}
