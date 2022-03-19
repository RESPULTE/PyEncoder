import typing
import enum
import sys

# TODO: a seperate config for each  + one main config


class DefaultBaseConfig:
    # MARKER CONFIGS
    MARKER = "\\"
    MARKER_BITSIZE = 8

    # ENCODED DATA CONFIGS
    ENCODED_DATA_MARKER_BITSIZE = 64

    # HEADER CONFIGS
    MAX_CODELENGTH = 16
    CODELENGTH_BITSIZE = 8
    HEADER_MARKER_BITSIZE = 32

    # DTYPE CONFIGS
    DTYPE_MARKER_BITSIZE = 8
    _SUPPORTED_DTYPE = typing.Literal["h", "i", "l", "q", "f", "d", "s"]  # for type-checking

    # MISC CONFIGS
    ENDIAN = "big"
    STRING_ENCODING_FORMAT = "utf-8"

    __all__ = list(set(vars().keys()) - {"__module__", "__qualname__"})

    def __init__(self, file_location: str, name: str):
        sys.modules[file_location + name] = self
        self.__generate_dtype_codebook(self.DTYPE_MARKER_BITSIZE)

    @classmethod
    def setup(cls, file_location, name: str = ".config"):
        return cls(file_location, name)

    @property
    def SUPPORTED_DTYPE(self) -> typing.List[str]:
        return typing.get_args(self._SUPPORTED_DTYPE)

    def __generate_dtype_codebook(self, dtype_bitsize: int):
        self.SUPPORTED_DTYPE_CODEBOOK = enum.Enum(
            "SUPPORTED_DTYPE_CODEBOOK",
            [
                (dtype, format(index, f"0{dtype_bitsize}b"))
                for index, dtype in enumerate(typing.get_args(self.SUPPORTED_DTYPE))
            ],
        )

    def __setattr__(self, attr_name, val):
        if attr_name == "DTYPE_MARKER_BITSIZE" and "SUPPORTED_DTYPE_CODEBOOK" in self.__dict__:
            self.__generate_dtype_codebook(dtype_bitsize=val)
        elif attr_name == "MARKER_BITSIZE" and "MARKER_BITSIZE" in self.__dict__:
            if len(format(self.MARKER, "b")) > val:
                raise ValueError("bruh")

        super().__setattr__(attr_name, val)


DefaultBaseConfig.setup(__name__.split(".")[0])
