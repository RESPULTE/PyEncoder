# -----------------------------------------------MARKER CONFIGS--------------------------------------------------
SOF_MARKER = "\x0f"
EOF_MARKER = "\x0f"

MARKER_DTYPE = "s"
MARKER_BITSIZE = 24

# -------------------------------------------ENCODED DATA CONFIGS-------------------------------------------------
LENGTH_ENCODING_DATA_DTYPE = "B"

# ---------------------------------------------HEADER CONFIGS------------------------------------------------------
MAX_CODELENGTH = 16
CODELENGTH_BITSIZE = 8
SYMBOL_BITSIZE = 8
CODELENGTH_DTYPE = "H"

HEADER_MARKER_BITSIZE = 64
HEADER_MARKER_DTYPE = "Q"

# ---------------------------------------------DTYPE CONFIGS------------------------------------------------------
CTYPE_INT_DTYPE_BITSIZE = {
    # --- char ---#
    "b": 8,
    "B": 8,
    # --- short ---#
    "h": 16,
    "H": 16,
    # --- integer ---#
    "i": 32,
    "I": 32,
    # --- long ---#
    "l": 32,
    "L": 32,
    # --- long ---#
    "q": 64,
    "Q": 64,
}
ENDIAN = "big"

__all__ = [v for v in vars().keys() if not v.startswith("__") and v.isupper()]
