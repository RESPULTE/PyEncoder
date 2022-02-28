import struct
from typing import Iterable, List, Any, Literal, NewType, Tuple, Union, Type

from pyencoder._type_hints import BinaryCode

Matrix2D = NewType("Matrix2D", List[List[Any]])


def zigzag(dataset: Matrix2D, runtype: Literal["d", "h", "v"], inverse: bool = False) -> List[Any]:
    if inverse and not all(isinstance(data, Iterable) for data in dataset):
        raise ValueError("Invalid dataset, dataset must a 1D/non-nested iterable")

    if not inverse and not isinstance(dataset, Iterable):
        raise ValueError("Invalid dataset, dataset must a 2D/nested iterable")

    valid_runtypes = {"d": generate_dzigzag_index, "h": generate_hzigzag_index, "v": generate_vzigzag_index}
    row, col = len(dataset), len(dataset[0])
    index_list = valid_runtypes[runtype](row, col)

    if not inverse:
        return [dataset[i][j] for (i, j) in index_list]

    matrix_2D = [[None for _ in range(col)] for _ in range(row)]

    for index, (i, j) in enumerate(index_list):
        matrix_2D[i][j] = dataset[index]

    return matrix_2D


def generate_dzigzag_index(row, col):
    index_list = [[] for _ in range(row + col - 1)]

    for i in range(row):
        for j in range(col):
            index_sum = i + j
            if index_sum % 2 == 0:
                index_list[index_sum].insert(0, (i, j))
                continue
            index_list[index_sum].append((i, j))

    return [(i, j) for coor in index_list for (i, j) in coor]


def generate_vzigzag_index(row: int, col: int) -> List[Tuple[int, int]]:
    datapacks = []

    for j in range(col):
        insert_index = j * col
        for i in range(row):
            if j % 2 == 0:
                datapacks.append((i, j))
                continue
            datapacks.insert(insert_index, (i, j))

    return datapacks


def generate_hzigzag_index(row: int, col: int) -> List[Tuple[int, int]]:
    datapacks = []

    for i in range(row):
        insert_index = i * row
        for j in range(col):
            if i % 2 == 0:
                datapacks.append((i, j))
                continue
            datapacks.insert(insert_index, (i, j))

    return datapacks


def tobin(data: Union[int, float, str], dtype: Type, bitlength: int = 1, **kwargs) -> BinaryCode:
    data2bin_converter = {str: char2bin, int: int2bin, float: float2bin}

    if dtype not in data2bin_converter.keys():
        raise TypeError(f"data type not supported: '{dtype.__name__}'")

    return data2bin_converter[dtype](data=data, bitlength=bitlength, **kwargs)


def frombin(data: BinaryCode, dtype: Union[int, float, str], **kwargs) -> Union[int, float, str]:
    bin2data_converter = {str: bin2char, int: bin2int, float: bin2float}
    if dtype not in bin2data_converter.keys():
        raise TypeError(f"data type not supported: '{dtype.__name__}'")

    return bin2data_converter[dtype](b=data, **kwargs)


def bin2float(b: BinaryCode, decimal: int, signed: bool = False) -> float:
    float_repr = list(str(bin2int(b, signed=signed)))

    decimal_index = len(float_repr) - decimal
    float_repr[decimal_index:decimal_index] = "."

    return float("".join(float_repr))


def float2bin(data: float, decimal: int, bitlength: int = 0, signed: bool = False) -> BinaryCode:
    return int2bin(int(format(data, f".{decimal}f").replace(".", "")), bitlength, signed)


def char2bin(data: str, bitlength: int) -> BinaryCode:
    return format(ord(data), f"0{bitlength}b")


def bin2char(b: BinaryCode) -> str:
    return chr(int(b, 2))


def int2bin(data: int, bitlength: int = 0, signed: bool = False) -> BinaryCode:
    bin_int = format(data, f"0{bitlength}b")
    if not signed:
        return bin_int

    if data > 0:
        return "0" + bin_int
    return "1" + bin_int[1:]


def bin2int(b: BinaryCode, signed: bool = False) -> int:
    if not signed:
        return int(b, 2)

    sign_bit = b[0]
    i = int(b[1:], 2)
    return -i if sign_bit == "1" else i


def tobytes(data: Union[int, float, str]) -> bytes:
    data2byte_converter = {
        str: ("s", data),
        int: ("i", data),
        float: ("f", data),
    }
    dtype = type(data)
    if dtype not in data2byte_converter.keys():
        raise TypeError(f"data type not supported: '{dtype.__name__}'")

    return struct.pack(*data2byte_converter[dtype])


def frombytes(bytedata: bytes, dtype: Union[int, float, str]) -> Union[int, float, str]:
    byte2data_converter = {
        str: ("s", bytedata),
        int: ("i", bytedata),
        float: ("f", bytedata),
    }
    if dtype not in byte2data_converter.keys():
        raise TypeError(f"data type not supported: '{dtype.__name__}'")

    return struct.unpack(*byte2data_converter[dtype])[0]
