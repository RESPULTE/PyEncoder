import struct
from bitarray import bitarray
from collections import deque
from typing import Any, Iterable, List, Literal, NewType, Optional, Tuple, Type, Union

from pyencoder.type_hints import Bitcode, ValidDataset, SupportedDataType
from pyencoder.config import ENDIAN, ENDIAN_SYMBOL, STRING_ENCODING_FORMAT

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


def tobin(data: ValidDataset, dtype: SupportedDataType, bitlength: Optional[int] = 0) -> Bitcode:
    if dtype == "s":
        if isinstance(data, list):
            data = "".join(data)
        byte_data = str.encode(data, STRING_ENCODING_FORMAT)
    else:
        if not isinstance(data, Iterable):
            data = [data]
        byte_data = struct.pack("%s%s%s" % (ENDIAN_SYMBOL, len(data), dtype), *data)

    bindata = "".join("{:08b}".format(b) for b in byte_data)
    binlen = len(bindata)

    if bitlength == 0:
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


def frombin(data: Bitcode, dtype: SupportedDataType, num: int) -> ValidDataset:
    """converts a string of 0 and 1 back into the original data

    Args:
        data (BinaryCode): a string of 0 and 1
        dtype (Union[int, float, str]): the desired data type to convert to

    Raises:
        TypeError: if the desired datatype is not of the integer, floats or strings data type

    Returns:
        Union[int, float, str]: converted data
    """
    byte_data = int(data, 2).to_bytes((len(data) + 7) // 8, byteorder=ENDIAN)

    if dtype == "s":
        decoded_data = "".join(bytes.decode(byte_data, STRING_ENCODING_FORMAT))
    else:
        decoded_data = list(struct.unpack("%s%s%s" % (ENDIAN_SYMBOL, num, dtype), byte_data))
        if dtype == "f":
            decoded_data = [round(f, 5) for f in decoded_data]

    return decoded_data


def partition_bitarray(
    bitstring: bitarray,
    delimiter: Bitcode = None,
    index: Union[List[int], int] = None,
    continuous: Optional[bool] = False,
) -> List[bitarray]:
    if (index is None and delimiter is None) or (index != None and delimiter != None):
        raise ValueError("either an index or a delimiter is required")

    if delimiter:
        left_end = bitstring.index(bitarray(delimiter))
        right_start = left_end + len(delimiter)
        return bitstring[:left_end], bitstring[right_start:]

    if not isinstance(index, Iterable):
        return bitstring[:index], bitstring[index:]

    to_process = deque(index)
    # add comment later i forgorr what this thing does
    sections = []
    prev_index = 0
    while to_process:
        curr_index = to_process.popleft()
        if not continuous:
            curr_index = curr_index - prev_index
        sections.append(bitstring[:curr_index])
        bitstring = bitstring[curr_index:]
        prev_index = curr_index

    sections.append(bitstring)

    return sections


# TODO: ADD MORE DATA TYPE TO THE "tobin" & "frombin" functions
