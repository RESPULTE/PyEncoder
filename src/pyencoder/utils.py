import re
import struct
from bitarray import bitarray
from typing import Any, Iterable, List, Literal, NewType, Optional, Tuple, Type, Union

from numpy import sign

from pyencoder._type_hints import BitCode

Matrix2D = NewType("Matrix2D", List[List[Any]])


def zigzag(
    dataset: Matrix2D, runtype: Literal["d", "h", "v"], inverse: Optional[bool] = False
) -> Union[List[List[Any]], List[Any]]:
    """generates a 1D array from a 2D array with the given runtype in a zig-zaggy fashion

    Args:
        dataset (Matrix2D): a 2D matrix which is a list made up of lists (nested list),
                            that is symmetrical in its rows & columns

        runtype (Literal['d', 'h', 'v']): traverses the given 2D matrix in the given runtype
                                          'd' (diagonal): - traverse in a sideway Z pattern
                                          'h' (horizontal): - traverse in a 'normal' Z pattern
                                          'v' (vertical): - traverse in a N pattern

        inverse (bool, optional): recreates a 1D dataset into 2D array in a zig zaggy fashion. Defaults to False.

    Raises:
        ValueError: if inverse is True, but the given dataset is not an iterable list
        ValueError: if the element in the 2D dataset is not iterables, i.e not a nested list
        ValueError: if the given 2D dataset is not symmetrical

    Returns:
        List[Any]: if the inverse is False
        List[List[Any]]: if the inverse is True
    """
    if inverse and not isinstance(dataset, Iterable):
        raise ValueError("dataset must a 1D/non-nested iterable")

    if not inverse:
        if not all(isinstance(data, Iterable) for data in dataset):
            raise ValueError("dataset must a 2D/nested iterable")
        if sum(len(row) for row in dataset) % len(dataset[0]) != 0:
            raise ValueError(
                "Invalid dataset: dataset must be symmetrical, each row must have the same number of columns"
            )

    valid_runtypes = {"d": generate_dzigzag_index, "h": generate_hzigzag_index, "v": generate_vzigzag_index}
    row, col = len(dataset), len(dataset[0])
    index_list = valid_runtypes[runtype](row, col)

    if not inverse:
        return [dataset[i][j] for (i, j) in index_list]

    matrix_2D = [[None for _ in range(col)] for _ in range(row)]

    for index, (i, j) in enumerate(index_list):
        matrix_2D[i][j] = dataset[index]

    return matrix_2D


def generate_dzigzag_index(row: int, col: int) -> List[Tuple[int, int]]:
    """generate all the required indexes to turn a 2D array
       into a 1D array in a zig-zaggy fashion in a shape of a sideway Z

    Args:
        row (int): number of row in the 2D array
        col (int): number of columns in the 2D array

    Returns:
        List[Tuple[int, int]]: a list of tupe of indexes, (i, j)
    """
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
    """generate all the required indexes to turn a 2D array
       into a 1D array in a zig-zaggy fashion in a shape of the 'N' letter

    Args:
        row (int): number of row in the 2D array
        col (int): number of columns in the 2D array

    Returns:
        List[Tuple[int, int]]: a list of tupe of indexes, (i, j)
    """
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
    """generate all the required indexes to turn a 2D array
       into a 1D array in a zig-zaggy fashion in a shape of the 'Z' letter

    Args:
        row (int): number of row in the 2D array
        col (int): number of columns in the 2D array

    Returns:
        List[Tuple[int, int]]: a list of tupe of indexes, (i, j)
    """
    datapacks = []

    for i in range(row):
        insert_index = i * row
        for j in range(col):
            if i % 2 == 0:
                datapacks.append((i, j))
                continue
            datapacks.insert(insert_index, (i, j))

    return datapacks


def tobin(data: Union[int, float, str], bitlength: Optional[int] = 0, dtype: Optional[Type] = None) -> BitCode:
    """converts the given data into binary string of 0s andd 1s

    Args:
        data (Union[int, float, str]): integer, floats and strings are the only accepted data types

    Raises:
        TypeError: if the given data is not of the integer, floats or strings data type

    Returns:
        BinaryCode: a string of 0 and 1
    """
    data2bin_config = {
        str: lambda x: str.encode(x, "utf-8"),
        int: lambda x: struct.pack(">h", x),
        float: lambda x: struct.pack(">f", x),
    }

    dtype = type(data) if not dtype else dtype
    if dtype not in data2bin_config.keys():
        raise TypeError(f"data type not supported: '{dtype.__name__}'")

    bindata = "".join("{:08b}".format(b) for b in data2bin_config[dtype](data))
    binlen = len(bindata)

    if binlen > bitlength:
        return bindata.removeprefix("0" * (binlen - bitlength))

    return bindata.zfill(bitlength)


def frombin(data: BitCode, dtype: Union[int, float, str]) -> Union[int, float, str]:
    """converts a string of 0 and 1 back into the original data

    Args:
        data (BinaryCode): a string of 0 and 1
        dtype (Union[int, float, str]): the desired data type to convert to

    Raises:
        TypeError: if the desired datatype is not of the integer, floats or strings data type

    Returns:
        Union[int, float, str]: converted data
    """
    bin2data_converter = {
        str: lambda x: bytes.decode(x, "utf8"),
        int: lambda x: struct.unpack(">h", x)[0],
        float: lambda x: round(struct.unpack(">f", x)[0], 3),
    }

    if dtype not in bin2data_converter.keys():
        raise TypeError(f"data type not supported: '{dtype.__name__}'")

    byte_data = int(data, 2).to_bytes((len(data) + 7) // 8, byteorder="big")

    return bin2data_converter[dtype](byte_data)


def partition_bitarray(bitstring: bitarray, delimiter: BitCode = None, index: int = None) -> Tuple[bitarray, bitarray]:
    """a helper function to parition the bitarray into two parts with the given delimeter

    Args:
        bitstring (bitarray): an array containning 0 and 1
        delimiter (BinaryCode): string containning 1 and 0

    Returns:
        Tuple[bitarray, bitarray]: two part of the seperated bitarray
    """
    if (not index and not delimiter) or (index and delimiter):
        raise ValueError("either an index or a delimiter is required")

    left_end = right_start = index

    if delimiter:
        left_end = bitstring.index(bitarray(delimiter))
        right_start = left_end + len(delimiter)

    return bitstring[:left_end], bitstring[right_start:]
