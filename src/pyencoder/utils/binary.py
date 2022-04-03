import re
import struct
from collections import deque
from turtle import right
from typing import List, Iterable, Optional, Sequence, Tuple, Type, Union, overload

from numpy import isin

from pyencoder import config
from pyencoder.type_hints import Bitcode, ValidDataType, ValidDataset, SupportedDataType


@overload
def tobin(__data: ValidDataset, __dtype: Type[Union[int, float, str]], bitlength: Optional[int] = None) -> Bitcode:
    ...


@overload
def tobin(__data: ValidDataset, __dtype: SupportedDataType, bitlength: Optional[int] = None) -> Bitcode:
    ...


@overload
def tobin(__data: str, __dtype: str = "s", encoding: str = None) -> Bitcode:
    ...


def tobin(
    __data: ValidDataset,
    __dtype: Optional[SupportedDataType | bytes],
    bitlength: Optional[int] = None,
    *,
    encoding: Optional[str] = None,
    signed: bool = True,
) -> Bitcode:

    if __dtype is int:
        if not isinstance(__data, Iterable):
            __data = [__data]

        bindata = [None] * len(__data)
        if signed:
            for index, d in enumerate(__data):
                b = bin(d)
                b = "0" + b[2:] if d > 0 else b[3:]
                bindata[index] = b
        else:
            bindata = (bin(d)[2:] for d in __data)

    else:
        bindata = ("{:08b}".format(b) for b in tobytes(__data, __dtype))

    bindata = "".join(bindata)
    binlen = len(bindata)

    if bitlength is None:
        return bindata

    elif bitlength == -1:
        if all(b == "0" for b in bindata):
            return "0"
        elif signed:
            return "0" + bindata.lstrip("0")
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
def frombin(__data: ValidDataset, __dtype: Type[Union[int, float, str]], num: int = 1) -> ValidDataset:
    ...


@overload
def frombin(__data: ValidDataset, __dtype: SupportedDataType, num: int = 1) -> ValidDataset:
    ...


@overload
def frombin(__data: str, __dtype: str = "s", num: Optional[int] = None, encoding: Optional[str] = None) -> ValidDataset:
    ...


def frombin(
    __data: Bitcode,
    __dtype: SupportedDataType | bytes,
    num: int = 1,
    *,
    encoding: Optional[str] = None,
    signed: bool = True,
) -> ValidDataset:
    """converts a string of 0 and 1 back into the original data

    Args:
        data (BinaryCode): a string of 0 and 1
        dtype (Union[int, float, str]): the desired data type to convert to

    Raises:
        TypeError: if the desired datatype is not of the integer, floats or strings data type

    Returns:
        Union[int, float, str]: converted data
    """
    if __dtype is int:
        stop = len(__data)
        step = stop // num
        decoded_data = [None] * num
        for index, i in enumerate(range(0, stop, step)):
            bindata = __data[i : i + step]
            decoded_data[index] = int("-%s" % (bindata) if bindata[0] == "1" else bindata, 2)

        return decoded_data if num != 1 else decoded_data[0]

    bytedata = int(__data, 2).to_bytes((len(__data) + 7) // 8, config.ENDIAN)
    if __dtype in ("s", str):
        return "".join(bytes.decode(bytedata, encoding or config.DEFAULT_STR_FORMAT))

    else:
        try:
            decoded_data = list(
                struct.unpack("%s%s%s" % (">" if config.ENDIAN == "big" else "<", num, __dtype), bytedata)
            )
            return decoded_data if num != 1 else decoded_data[0]
        except struct.error:
            raise TypeError(f"cannot convert byte data to '{__dtype}'")


def tobytes(
    __data: ValidDataset,
    __dtype: Optional[SupportedDataType | Bitcode],
    bytelength: Optional[int] = None,
    *,
    encoding: Optional[str] = None,
    signed: bool = True,
) -> bytes:

    if __dtype in ("s", str):
        bytedata = str.encode(__data, encoding or config.DEFAULT_STR_FORMAT)

    elif __dtype == "bin":
        bytedata = int(__data, 2).to_bytes((len(__data) + 7) // 8, config.ENDIAN, signed=signed)

    elif __dtype == int:
        bytedata = int.to_bytes(__data, (__data.bit_length() + 7) // 8, config.ENDIAN, signed=signed)

    else:
        if __dtype == float:
            __dtype = config.DEFAULT_FLOAT_FORMAT

        else:
            try:
                config.CTYPE_INT_DTYPE_BITSIZE[__dtype]
            except KeyError:
                raise TypeError(f"invalid data type: {__dtype}")

        if isinstance(__data, Iterable):
            bytedata = struct.pack("%s%s%s" % (">" if config.ENDIAN == "big" else "<", len(__data), __dtype), *__data)
        else:
            bytedata = struct.pack("%s%s" % (">" if config.ENDIAN == "big" else "<", __dtype), __data)

    encoded_bytelen = len(bytedata)

    if bytelength is None:
        return bytedata

    elif bytelength == -1:
        if signed:
            return bytes(1) + bytedata.lstrip(bytes(1))
        return bytedata.lstrip(bytes(1))

    elif encoded_bytelen > bytelength:
        actual_binlen = len(bytedata.lstrip(bytes(1)))
        if actual_binlen > bytelength:
            raise ValueError(f"data's bytelength({actual_binlen}) is longer than the given bytelength({bytelength})")
        bytedata = bytedata.removeprefix(bytes(1) * (encoded_bytelen - bytelength))

    elif encoded_bytelen < bytelength:
        bytedata = bytes(bytelength - encoded_bytelen) + bytedata

    return bytedata


def frombytes(
    __data: bytes,
    __dtype: SupportedDataType | Bitcode,
    num: int = 1,
    *,
    encoding: Optional[str] = None,
    signed: bool = True,
) -> ValidDataset:
    """converts a string of 0 and 1 back into the original data

    Args:
        __data (BinaryCode): a string of 0 and 1
        __dtype (Union[int, float, str]): the desired data type to convert to

    Raises:
        TypeError: if the desired datatype is not of the integer, floats or strings data type

    Returns:
        Union[int, float, str]: converted data
    """

    if __dtype is int:
        stop = len(__data)
        step = stop // num
        decoded_data = [
            int.from_bytes(__data[i : i + step], config.ENDIAN, signed=signed) for i in range(0, stop, step)
        ]
        return decoded_data if num != 1 else decoded_data[0]

    if __dtype in ("s", str):
        return "".join(bytes.decode(__data, encoding or config.DEFAULT_STR_FORMAT))

    elif __dtype == "bin":
        return "".join("{:08b}".format(b) for b in __data)

    else:
        try:
            decoded_data = list(
                struct.unpack("%s%s%s" % (">" if config.ENDIAN == "big" else "<", num, __dtype), __data)
            )
            return decoded_data if num != 1 else decoded_data[0]
        except struct.error:
            raise TypeError(f"cannot convert byte data to '{__dtype}'")


def xsplit(
    __s: str,
    delimiter: Optional[List[str] | str] = None,
    index: Optional[List[int] | int] = None,
    *,
    continuous: bool = False,
) -> List[str]:
    def findall(__s, __sub_s: str | Sequence[str]) -> List[Tuple[int, int]]:
        if not isinstance(__sub_s, (list, tuple)):
            __sub_s = [__sub_s]
        return [mo.span() for sub_s in __sub_s for mo in re.finditer(f"({sub_s})", __s)]

    if (index is None and delimiter is None) or (index != None and delimiter != None):
        raise ValueError("either an index or a delimiter is required")

    if not delimiter and not isinstance(index, Iterable):
        index = [index]

    to_process = deque(findall(__s, delimiter) if not index else index)
    prev_index = 0
    sections = []

    if index:
        while to_process:
            curr_index = to_process.popleft()

            section_to_append = __s[:curr_index]

            if continuous:
                __s = __s[curr_index:]
                prev_index = 0

            sections.append(section_to_append[prev_index:])
            prev_index = curr_index

        last_section = __s[prev_index:] if not continuous else __s
        sections.append(last_section)
        return sections

    while to_process:
        left_end, right_start = to_process.popleft()

        section_to_append = __s[:left_end]

        if continuous:
            __s = __s[right_start:]
            prev_index = 0

        sections.append(section_to_append[prev_index:])
        prev_index = right_start

    last_section = __s[prev_index:] if not continuous else __s
    sections.append(last_section)
    return sections
