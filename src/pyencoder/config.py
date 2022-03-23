from typing import Literal, get_args
from enum import Enum

# -----------------------------------------------MARKER CONFIGS--------------------------------------------------
SOF_MARKER = "\\"
EOF_MARKER = "\\"

MARKER_DTYPE = "s"
MARKER_BITSIZE = 8

# -------------------------------------------ENCODED DATA CONFIGS-------------------------------------------------
ENCODED_DATA_MARKER_BITSIZE = 64
LENGTH_ENCODING_DATA_DTYPE = "B"

# ---------------------------------------------HEADER CONFIGS------------------------------------------------------
MAX_CODELENGTH = 16
CODELENGTH_BITSIZE = 8
CODELENGTH_DTYPE = "H"

HEADER_MARKER_BITSIZE = 32
HEADER_MARKER_DTYPE = "I"

# ---------------------------------------------DTYPE CONFIGS------------------------------------------------------
DTYPE_MARKER_BITSIZE = 8
SUPPORTED_DTYPE = ["b", "B", "h", "H", "i", "I", "l", "L", "q", "Q", "f", "d", "s"]

SUPPORTED_DTYPE_CODEBOOK: Enum = Enum(
    "SUPPORTED_DTYPE_CODEBOOK",
    [(dtype, format(index, f"0{DTYPE_MARKER_BITSIZE}b")) for index, dtype in enumerate(SUPPORTED_DTYPE)],
)

# ----------------------------------------------MISC CONFIGS-------------------------------------------------------
ENDIAN = "big"
STRING_ENCODING_FORMAT = "utf-8"


__all__ = [v for v in vars().keys() if not v.startswith("__") and v.isupper()]
