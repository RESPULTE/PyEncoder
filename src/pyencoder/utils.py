import struct
from bitarray import bitarray
from typing import Any, Iterable, List, Literal, NewType, Optional, Tuple, Type, Union

from pyencoder._type_hints import BinaryCode

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
        raise ValueError("Invalid dataset, dataset must a 1D/non-nested iterable")

    if not inverse:
        if all(isinstance(data, Iterable) for data in dataset):
            raise ValueError("Invalid dataset, dataset must a 2D/nested iterable")
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


def tobin(data: Union[int, float, str], **kwargs) -> BinaryCode:
    """converts the given data into binary string of 0s andd 1s

    Args:
        data (Union[int, float, str]): integer, floats and strings are the only accepted data types

    Raises:
        TypeError: if the given data is not of the integer, floats or strings data type

    Returns:
        BinaryCode: a string of 0 and 1
    """
    data2bin_converter = {str: char2bin, int: int2bin, float: float2bin}

    dtype = type(data)

    if dtype not in data2bin_converter.keys():
        raise TypeError(f"data type not supported: '{dtype.__name__}'")

    return data2bin_converter[dtype](data=data, **kwargs)


def frombin(data: BinaryCode, dtype: Union[int, float, str], **kwargs) -> Union[int, float, str]:
    """converts a string of 0 and 1 back into the original data

    Args:
        data (BinaryCode): a string of 0 and 1
        dtype (Union[int, float, str]): the desired data type to convert to

    Raises:
        TypeError: if the desired datatype is not of the integer, floats or strings data type

    Returns:
        Union[int, float, str]: converted data
    """
    bin2data_converter = {str: bin2char, int: bin2int, float: bin2float}
    if dtype not in bin2data_converter.keys():
        raise TypeError(f"data type not supported: '{dtype.__name__}'")

    return bin2data_converter[dtype](b=data, **kwargs)


def bin2float(b: BinaryCode, decimal: int, signed: bool = False) -> float:
    """converts a string of 0 and 1 into float

    Args:
        b (BinaryCode): a string of 0 and 1

        decimal (int): the number of decimal places to convert to

        signed (bool, optional): whether the float has a negative/positive sign. Defaults to False.

    Returns:
        float: a float data
    """
    float_repr = list(str(bin2int(b, signed=signed)))
    decimal_index = len(float_repr) - decimal
    float_repr[decimal_index:decimal_index] = "."

    return float("".join(float_repr))


def float2bin(data: float, decimal: int, bitlength: int = 0, signed: bool = False) -> BinaryCode:
    """converts float into a string of 1 and 0
       - Done by first formatting it with the given decimal places and
         converting it into integer by removing the decimal point

    Args:
        data (float): a float data
        decimal (int): formats the float into the number of given decimal places

        bitlength (int, optional): an optional parameter to pad the binary string to the given length.
                                   if the generated string is longer than the given length, no changes will be made.
                                   Defaults to 0.

        signed (bool, optional): whether the float data has negative/positive sign. Defaults to False.

    Returns:
        BinaryCode: a string of 0 and 1
    """
    return int2bin(int(format(data, f".{decimal}f").replace(".", "")), bitlength, signed)


def char2bin(data: str, bitlength: int = 0) -> BinaryCode:
    """converts a single unicode string character into a binary string of 0 and 1

    Args:
        data (str): a string of 0 and 1
        bitlength (int, optional): an optional parameter to pad the binary string to the given length.
                                   if the generated string is longer than the given length, no changes will be made.
                                   Defaults to 0.

    Returns:
        BinaryCode: a string of 0 and 1
    """
    return format(ord(data), f"0{bitlength}b")


def bin2char(b: BinaryCode) -> str:
    """converts a string of 0 and 1 into a single unicode character

    Args:
        b (BinaryCode): a string of 0 and 1

    Returns:
        str: a single unicode character
    """
    return chr(int(b, 2))


def int2bin(data: int, bitlength: int = 0, signed: bool = False) -> BinaryCode:
    """converts an integer into a binary string

    Args:
        data (int): an integer data

        bitlength (int, optional): an optional parameter to pad the binary string to the given length.
                                   if the generated string is longer than the given length, no changes will be made.
                                   Defaults to 0.

        signed (bool, optional):  whether the integer data has negative/positive sign. Defaults to False.

    Returns:
        BinaryCode: a string of 0 and 1
    """
    bin_int = format(data, f"0{bitlength}b")
    if not signed:
        return bin_int

    if data > 0:
        return "0" + bin_int
    return "1" + bin_int[1:]


def bin2int(b: BinaryCode, signed: bool = False) -> int:
    """converts a string of 0 and 1 into an integer


    Args:
        b (BinaryCode): a string of 0 and 1
        signed (bool, optional): whether the integer data has negative/positive sign. Defaults to False.

    Returns:
        int: an integer data
    """
    if not signed:
        return int(b, 2)

    sign_bit = b[0]
    i = int(b[1:], 2)
    return -i if sign_bit == "1" else i


def tobytes(data: Union[int, float, str]) -> bytes:
    """converts the given data into python built-in byte type

    Args:
        data (Union[int, float, str]): data

    Raises:
        TypeError: if the given data is not of the integer, floats or strings data type

    Returns:
        bytes: a python built-in byte type data
    """
    data2byte_converter = {
        str: "s",
        int: "i",
        float: "f",
    }
    dtype = type(data)
    if dtype == str:
        data = data.encode("utf-8")

    if dtype not in data2byte_converter.keys():
        raise TypeError(f"data type not supported: '{dtype.__name__}'")

    return struct.pack(data2byte_converter[dtype], data)


def frombytes(bytedata: bytes, dtype: Union[int, float, str]) -> Union[int, float, str]:
    """converts byte into data with the given data type

    Args:
        bytedata (bytes): a python built-in byte type
        dtype (Union[int, float, str]): data type

    Raises:
        TypeError: if the given data type is not of the integer, floats or string

    Returns:
        Union[int, float, str]: converted data in the given data type
    """
    byte2data_converter = {
        str: ("s", bytedata),
        int: ("i", bytedata),
        float: ("f", bytedata),
    }
    if dtype not in byte2data_converter.keys():
        raise TypeError(f"data type not supported: '{dtype.__name__}'")

    return struct.unpack(*byte2data_converter[dtype])[0]


def partition_bitarray(
    bitstring: bitarray, delimiter: BinaryCode = None, index: int = None
) -> Tuple[bitarray, bitarray]:
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
