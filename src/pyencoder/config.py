from typing import Dict, Type

ENCODING_MARKER = "\\"


_ENCODING_MARKER_SIZE = 32
_HEADER_MARKER_SIZE = 16
_ELEM_MARKER_SIZE = 8
_DTYPE_MARKER_SIZE = 2


_DECIMAL_MARKER_SIZE = 4
_MAX_DECIMAL = 15


_SUPPORTED_DTYPE_TO_BIN: Dict[Type, str] = {str: "01", int: "10", float: "11"}
_SUPPORTED_DTYPE_FROM_BIN: Dict[str, Type] = {"01": str, "10": int, "11": float}
