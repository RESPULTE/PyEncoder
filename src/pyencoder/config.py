from typing import Literal, get_args
from enum import Enum

# -----------------------------------------------MARKER CONFIGS--------------------------------------------------
MARKER = "\\"
MARKER_SIZE = 8

# -------------------------------------------ENCODED DATA CONFIGS-------------------------------------------------
ENCODED_DATA_MARKER_SIZE = 64

# ---------------------------------------------HEADER CONFIGS------------------------------------------------------
MAX_CODELENGTH = 16
CODELENGTH_BITSIZE = 8
HEADER_MARKER_SIZE = 32

# ---------------------------------------------DTYPE CONFIGS------------------------------------------------------
DTYPE_MARKER_SIZE = 8
SUPPORTED_DTYPE = Literal["h", "i", "l", "q", "f", "d", "s"]

SUPPORTED_DTYPE_CODEBOOK: Enum = Enum(
    "SUPPORTED_DTYPE_CODEBOOK",
    [(dtype, format(index, f"0{DTYPE_MARKER_SIZE}b")) for index, dtype in enumerate(get_args(SUPPORTED_DTYPE))],
)

# ----------------------------------------------MISC CONFIGS-------------------------------------------------------
ENDIAN = "big"
STRING_ENCODING_FORMAT = "utf-8"


def __getattr__(attr_name: str):
    if attr_name == "ENDIAN_SYMBOL":
        return ">" if ENDIAN == "big" else "<"
    elif attr_name == "MARKER_DTYPE":
        return "s" if isinstance(MARKER, str) else "i"


__all__ = [v for v in vars().keys() if not v.startswith("__") and v.isupper()]
