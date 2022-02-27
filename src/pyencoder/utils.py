import struct
from typing import Iterable, List, Any, Literal, NewType, Tuple, Union

from pyencoder.config import BYTEORDER
from pyencoder._type_hints import BinaryCode

Matrix2D = NewType("Matrix2D", List[List[Any]])


def zigzag(dataset: Matrix2D, runtype: Literal["d", "h", "v"], inverse: bool = False) -> List[Any]:
    valid_runtypes = {"d": (dzigzag, idzigzag), "h": (hzigzag, ihzigzag), "v": (vzigzag, ivzigzag)}

    if runtype not in valid_runtypes:
        raise ValueError(f"Invalid runtype: {runtype}")

    if not all(isinstance(data, Iterable) for data in dataset) or not isinstance(dataset, Iterable):
        raise ValueError("Invalid dataset, dataset must a 2D/nested iterable")

    selected_runtypes = valid_runtypes[runtype][0] if not inverse else valid_runtypes[runtype][1]

    return selected_runtypes(dataset)


def dzigzag(dataset: Matrix2D) -> List[Any]:
    index_list = generate_dzigzag_index(len(dataset), len(dataset[0]))
    return [dataset[i][j] for (i, j) in index_list]


def idzigzag(dataset: Matrix2D) -> List[Any]:
    col = row = int(len(dataset) ** 0.5)

    matrix_2D = [[None for _ in range(col)] for _ in range(row)]

    for index, (i, j) in enumerate(generate_dzigzag_index(row, col)):
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


def vzigzag(dataset: Matrix2D) -> List[Any]:
    index_list = generate_vzigzag_index(len(dataset), len(dataset[0]))
    return [dataset[i][j] for (i, j) in index_list]


def ivzigzag(dataset: Matrix2D) -> List[Any]:
    col = row = int(len(dataset) ** 0.5)

    matrix_2D = [[None for _ in range(col)] for _ in range(row)]

    for index, (i, j) in enumerate(generate_vzigzag_index(row, col)):
        matrix_2D[i][j] = dataset[index]

    return matrix_2D


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


def hzigzag(dataset: Matrix2D) -> List[Any]:
    index_list = generate_hzigzag_index(len(dataset), len(dataset[0]))
    return [dataset[i][j] for (i, j) in index_list]


def ihzigzag(dataset: Matrix2D) -> List[Any]:
    col = row = int(len(dataset) ** 0.5)

    matrix_2D = [[None for _ in range(col)] for _ in range(row)]

    for index, (i, j) in enumerate(generate_hzigzag_index(row, col)):
        matrix_2D[i][j] = dataset[index]

    return matrix_2D


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


def tobin(data: Union[int, float, str], bitlength: int = 1, **kwargs) -> BinaryCode:
    data2bin_converter = {str: char2bin, int: int2bin, float: float2bin}
    dtype = type(data)
    if dtype not in data2bin_converter.keys():
        raise TypeError(f"data type not supported: '{dtype.__name__}'")

    return data2bin_converter[dtype](data, bitlength, **kwargs)


def frombin(binarydata: BinaryCode, dtype: Union[int, float, str], **kwargs) -> Union[int, float, str]:
    bin2data_converter = {str: bin2char, int: bin2int, float: bin2float}
    if dtype not in bin2data_converter.keys():
        raise TypeError(f"data type not supported: '{dtype.__name__}'")

    return bin2data_converter[dtype](binarydata, **kwargs)


def bin2float(b: BinaryCode) -> float:
    endian = ">" if BYTEORDER == "big" else "<"
    h = int(b, 2).to_bytes(8, byteorder=BYTEORDER)
    return struct.unpack(f"{endian}d", h)[0]


def float2bin(f: float, bitlength: int) -> BinaryCode:
    endian = ">" if BYTEORDER == "big" else "<"
    d = struct.unpack(f"{endian}Q", struct.pack(f"{endian}d", f))
    return format(*d, f"0{bitlength}b")


def char2bin(s: str, bitlength: int) -> BinaryCode:
    return format(ord(s), f"0{bitlength}b")


def bin2char(b: BinaryCode) -> str:
    return chr(int(b, 2))


def int2bin(i: int, bitlength: int, signed: bool = False) -> BinaryCode:
    bin_int = format(i, f"0{bitlength}b")
    if not signed:
        return bin_int

    sign_bit = "0" if i > 0 else "1"
    return sign_bit + bin_int


def bin2int(b: BinaryCode, signed: bool = False) -> int:
    if not signed:
        return int(b, 2)

    sign_bit = b[0]
    i = int(b[1:], 2)
    return -i if sign_bit == "1" else i


def tobytes(data: Union[int, float, str]) -> bytes:
    data2byte_converter = {
        str: lambda data: data.encode("utf-8"),
        int: lambda data: bytes(data),
        float: lambda data: struct.pack("f", data),
    }
    dtype = type(data)
    if dtype not in data2byte_converter.keys():
        raise TypeError(f"data type not supported: '{dtype.__name__}'")

    return data2byte_converter[dtype](data)


def frombytes(bytedata: bytes, dtype: Union[int, float, str]) -> Union[int, float, str]:
    byte2data_converter = {
        str: lambda data: data.decode("utf-8"),
        int: lambda data: int.from_bytes(data, BYTEORDER),
        float: lambda data: struct.unpack("f", data)[0],
    }
    if dtype not in byte2data_converter.keys():
        raise TypeError(f"data type not supported: '{dtype.__name__}'")

    return byte2data_converter[dtype](bytedata)
