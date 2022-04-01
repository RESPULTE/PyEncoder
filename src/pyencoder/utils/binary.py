import struct
from collections import deque
from typing import List, Iterable, Optional, Sequence, Tuple, Type, Union, overload

from pyencoder import config
from pyencoder.type_hints import Bitcode, ValidDataType, ValidDataset, SupportedDataType


@overload
def tobin(data: ValidDataset, dtype: Type[Union[int, float, str]], bitlength: Optional[int] = None) -> Bitcode:
    ...


@overload
def tobin(data: ValidDataset, dtype: SupportedDataType, bitlength: Optional[int] = None) -> Bitcode:
    ...


@overload
def tobin(data: str, dtype: str = "s", encoding: str = None) -> Bitcode:
    ...


def tobin(
    data: ValidDataset, dtype: SupportedDataType, bitlength: Optional[int] = None, *, encoding: Optional[str] = None
) -> Bitcode:
    if not isinstance(data, bytes):
        data = tobytes(data, dtype)
    if isinstance(data, (list, tuple)) and isinstance(data[0], bytes):
        try:
            data = b"".join(data)
        except ValueError:
            raise TypeError("inconsistent data type in list of bytes")

    bindata = "".join("{:08b}".format(b) for b in data)
    binlen = len(bindata)

    if bitlength is None:
        return bindata

    elif bitlength == -1:
        return bindata.lstrip("0")

    elif binlen > bitlength:
        actual_binlen = len(bindata.lstrip("0"))
        if actual_binlen > bitlength:
            raise ValueError(f"data's bitlength({actual_binlen}) is longer than the given bitlength({bitlength})")
        bindata = bindata.removeprefix("0" * (binlen - bitlength))

    elif binlen < bitlength:
        bindata = bindata.zfill(bitlength)

    return bindata


@overload
def frombin(data: ValidDataset, dtype: Type[Union[int, float, str]], num: int = 1) -> ValidDataset:
    ...


@overload
def frombin(data: ValidDataset, dtype: SupportedDataType, num: int = 1) -> ValidDataset:
    ...


@overload
def frombin(data: str, dtype: str = "s", num: Optional[int] = None, encoding: Optional[str] = None) -> ValidDataset:
    ...


def frombin(data: Bitcode, dtype: SupportedDataType, num: int = 1, *, encoding: Optional[str] = None) -> ValidDataset:
    """converts a string of 0 and 1 back into the original data

    Args:
        data (BinaryCode): a string of 0 and 1
        dtype (Union[int, float, str]): the desired data type to convert to

    Raises:
        TypeError: if the desired datatype is not of the integer, floats or strings data type

    Returns:
        Union[int, float, str]: converted data
    """
    return frombytes(tobytes(data, "bin"), dtype, num, encoding=encoding)


def tobytes(
    data: ValidDataset, dtype: SupportedDataType, bytelength: Optional[int] = None, *, encoding: Optional[str] = None
) -> bytes:
    if dtype in ("s", str):
        if isinstance(data, list):
            data = "".join(data)
        bytedata = str.encode(data, encoding or config.DEFAULT_STR_FORMAT)
    elif dtype == "bin":
        bytedata = int(data, 2).to_bytes((len(data) + 7) // 8, config.ENDIAN)
    else:
        if dtype == float:
            dtype = config.DEFAULT_FLOAT_FORMAT
        elif dtype == int:
            dtype = config.DEFAULT_INT_FORMAT

        if not isinstance(data, Iterable):
            data = [data]
        bytedata = struct.pack("%s%s%s" % (">" if config.ENDIAN == "big" else "<", len(data), dtype), *data)

    encoded_bytelen = len(bytedata)

    if bytelength is None:
        return bytedata

    elif bytelength == -1:
        return bytedata.lstrip(bytes(1))

    elif encoded_bytelen > bytelength:
        actual_binlen = len(bytedata.lstrip(bytes(1)))
        if actual_binlen > bytelength:
            raise ValueError(f"data's bytelength({actual_binlen}) is longer than the given bytelength({bytelength})")
        bytedata = bytedata.removeprefix(bytes(1) * (encoded_bytelen - bytelength))

    elif bytedata < bytelength:
        bytedata = bytes(bytelength) + bytedata

    return bytedata


def frombytes(data: bytes, dtype: SupportedDataType, num: int = 1, *, encoding: Optional[str] = None) -> ValidDataset:
    """converts a string of 0 and 1 back into the original data

    Args:
        data (BinaryCode): a string of 0 and 1
        dtype (Union[int, float, str]): the desired data type to convert to

    Raises:
        TypeError: if the desired datatype is not of the integer, floats or strings data type

    Returns:
        Union[int, float, str]: converted data
    """

    if dtype is int:
        stop = len(data)
        step = stop // num
        return [int.from_bytes(data[i : i + step], config.ENDIAN) for i in range(0, stop, step)]

    if dtype in ("s", str):
        return "".join(bytes.decode(data, encoding or config.DEFAULT_STR_FORMAT))

    elif dtype == "bin":
        return "".join("{:08b}".format(b) for b in data)

    else:
        try:
            decoded_data = list(struct.unpack("%s%s%s" % (">" if config.ENDIAN == "big" else "<", num, dtype), data))
            return decoded_data if num != 1 else decoded_data[0]
        except struct.error:
            raise TypeError(f"cannot convert byte data to '{dtype}'")


import re


class Bitstring(str):
    def __new__(cls, b: Bitcode) -> "Bitstring":
        if isinstance(b, str) and not all(s in ("0", "1") for s in b):
            raise ValueError(f"{cls.__name__} should only be given 0s and 1s")
        return super().__new__(cls, b)

    @classmethod
    def frombytes(cls, b: bytes) -> "Bitstring":
        return cls("".join("{:08b}".format(b_data) for b_data in b))

    def tobytes(self) -> bytearray:
        return int(self, 2).to_bytes((len(self) + 7) // 8, byteorder=config.ENDIAN)

    def findall(self, s: "Bitstring" | Sequence["Bitstring"]) -> List[Tuple[int, int]]:
        if not isinstance(s, (list, tuple)):
            s = [s]
        return [mo.span() for sub_s in s for mo in re.finditer(f"({sub_s})", self)]

    def append(self, s: "Bitstring") -> "Bitstring":
        return type(self)(self + s)

    def insert(self, i: int, s: "Bitstring") -> "Bitstring":
        return type(self)(self[:i] + s + self[i:])

    def split(
        self,
        delimiter: Optional[List[Bitcode] | Bitcode] = None,
        index: Optional[List[int] | int] = None,
        continuous: bool = False,
    ) -> List["Bitstring"]:
        if (index is None and delimiter is None) or (index != None and delimiter != None):
            raise ValueError("either an index or a delimiter is required")

        if not delimiter and not isinstance(index, Iterable):
            index = [index]

        to_process = deque(self.findall(delimiter) if not index else index)
        prev_index = 0
        sections = []

        if index:
            while to_process:
                curr_index = to_process.popleft()

                section_to_append = self[:curr_index]

                if continuous:
                    self = self[curr_index:]
                    prev_index = 0

                sections.append(section_to_append[prev_index:])
                prev_index = curr_index

            last_section = self[prev_index:] if not continuous else self
            sections.append(last_section)
            return sections

        while to_process:
            left_end, right_start = to_process.popleft()

            section_to_append = self[:left_end]

            if continuous:
                self = self[right_start:]
                prev_index = 0

            sections.append(section_to_append[prev_index:])
            prev_index = right_start

        last_section = self[prev_index:] if not continuous else self
        sections.append(last_section)
        return sections

    def __getitem__(self, __i: int | slice) -> str:
        return type(self)(super().__getitem__(__i))

    def __repr__(self) -> str:
        return "%s(%s)" % (type(self).__name__, self)
