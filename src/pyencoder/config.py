# -----------------------------------------------MARKER CONFIGS--------------------------------------------------
SOF_MARKER = "辣"
EOF_MARKER = "柳"

MARKER_DTYPE = "s"
MARKER_BITSIZE = 32

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
DEFAULT_FORMAT = {int: "i", float: "d", str: "s"}

# ----------------------------------------------MISC CONFIGS-------------------------------------------------------
ENDIAN = "big"
DEFAULT_STR_FORMAT = "utf-8"
DEFAULT_FLOAT_DECIMAL = 5

__all__ = [v for v in vars().keys() if not v.startswith("__") and v.isupper()]
