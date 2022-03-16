from enum import Enum

# -------------------------------------------ENCODED DATA CONFIGS-------------------------------------------------
ENCODED_DATA_MARKER_SIZE = 64

# ---------------------------------------------HEADER CONFIGS------------------------------------------------------
MAX_CODELENGTH = 16
CODELENGTH_BITSIZE = 8
HEADER_MARKER_SIZE = 32

# ---------------------------------------------DTYPE CONFIGS------------------------------------------------------
DTYPE_MARKER_SIZE = 8
SUPPORTED_DTYPE_CODEBOOK: Enum = Enum(
    "SUPPORTED_DTYPE",
    [
        (dtype, format(index, f"0{DTYPE_MARKER_SIZE}b"))
        for index, dtype in enumerate(["h", "i", "l", "q", "f", "d", "s"])
    ],
)

# ----------------------------------------------MISC CONFIGS-------------------------------------------------------
ENDIAN = "big"
ENDIAN_SYMBOL = ">" if ENDIAN == "big" else "<"

MARKER = "\\"
MARKER_DTYPE = "s" if isinstance(MARKER, str) else "i"

STRING_ENCODING_FORMAT = "utf-8"
