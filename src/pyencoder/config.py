from typing import Dict, Type

DELIMITER = "哇"
HUFFMARKER = "哇"
BYTEORDER = "little"
_DECIMAL_MARKER_LEN = 8

_DATA_BINARYSIZE_MARKER_LEN = 8
_DATASIZEMARKER_LEN = 32
_DTYPEMARKER_LEN = 2


_SUPPORTED_DTYPE_TO_BIN: Dict[Type, str] = {
    str: "01",
    int: "10",
    float: "11",
}
_SUPPORTED_DTYPE_FROM_BIN: Dict[str, Type] = {"01": str, "10": int, "11": float}
