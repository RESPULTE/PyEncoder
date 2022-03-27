import struct
from collections import deque
from bitarray import bitarray
from functools import lru_cache
from typing import List, Iterable, Literal, NewType, Optional, Tuple, Type, TypeVar, Union, overload

from pyencoder import config
from pyencoder.type_hints import Bitcode, ValidDataType, ValidDataset, SupportedDataType

T = TypeVar("T")
Matrix2D = NewType("Matrix2D", List[List[T]])


@overload
def zigzag(dataset: Matrix2D, runtype: Literal["d", "h", "v"]) -> List[T]:
    ...


@overload
def zigzag(dataset: List[T], runtype: Literal["d", "h", "v"], row: int, col: int) -> Matrix2D:
    ...


def zigzag(
    dataset: Union[Matrix2D, List[T]], runtype: Literal["d", "h", "v"], row: int = -1, col: int = -1
) -> Union[Matrix2D, List[T]]:
    if all(isinstance(data, Iterable) for data in dataset):
        row, col = len(dataset), len(dataset[0])
        inverse = False
    else:
        dataset_size = len(dataset)
        if row * col != dataset_size:
            raise ValueError(f"cannot form {row}x{col} matrix with datset of size '{dataset_size}'")
        inverse = True

    valid_runtypes = {"d": generate_dzigzag_index, "h": generate_hzigzag_index, "v": generate_vzigzag_index}
    index_list = valid_runtypes[runtype](row, col)

    if not inverse:
        try:
            return [dataset[i][j] for (i, j) in index_list]
        except IndexError:
            raise ValueError("dataset is not symmetrical, row & column does not match")

    matrix = [[None for _ in range(col)] for _ in range(row)]

    for index, (i, j) in enumerate(index_list):
        matrix[i][j] = dataset[index]

    return matrix


@lru_cache
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


@lru_cache
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


@lru_cache
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


@overload
def tobin(data: ValidDataset, dtype: Type[Union[int, float, str]], bitlength: Optional[int] = None) -> Bitcode:
    ...


@overload
def tobin(data: ValidDataset, dtype: SupportedDataType, bitlength: Optional[int] = None) -> Bitcode:
    ...


def tobin(
    data: ValidDataset, dtype: Union[Type[Union[int, float, str]], SupportedDataType], bitlength: Optional[int] = None
) -> Bitcode:

    # might abstract out to config.py
    if isinstance(dtype, type):
        if dtype is int:
            dtype = "i"
        elif dtype is float:
            dtype = "d"
        elif dtype is not str:
            raise TypeError(f"invalid data type: '{dtype.__name__}'")

    if dtype == "s":
        if isinstance(data, list):
            data = "".join(data)
        byte_data = str.encode(data, config.STRING_ENCODING_FORMAT)
    else:
        if not isinstance(data, Iterable):
            data = [data]
        byte_data = struct.pack("%s%s%s" % (">" if config.ENDIAN == "big" else "<", len(data), dtype), *data)

    bindata = "".join("{:08b}".format(b) for b in byte_data)
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


def frombin(data: Bitcode, dtype: Union[Type[Union[int, float, str]], SupportedDataType], num: int = 1) -> ValidDataset:
    """converts a string of 0 and 1 back into the original data

    Args:
        data (BinaryCode): a string of 0 and 1
        dtype (Union[int, float, str]): the desired data type to convert to

    Raises:
        TypeError: if the desired datatype is not of the integer, floats or strings data type

    Returns:
        Union[int, float, str]: converted data
    """
    byte_data = int(data, 2).to_bytes((len(data) + 7) // 8, byteorder=config.ENDIAN)

    # might abstract out to config.py
    if isinstance(dtype, type):
        if dtype is int:
            return int(data, 2)
        elif dtype is float:
            dtype = "d"
        elif dtype is not str:
            raise TypeError(f"invalid data type: '{dtype.__name__}'")

    if dtype == "s":
        decoded_data = "".join(bytes.decode(byte_data, config.STRING_ENCODING_FORMAT))
    else:
        decoded_data = list(struct.unpack("%s%s%s" % (">" if config.ENDIAN == "big" else "<", num, dtype), byte_data))
        if dtype == "f":
            decoded_data = [round(f, 5) for f in decoded_data]

    return decoded_data if num != 1 else decoded_data[0]


@overload
def partition_bitarray(bitarray_: bitarray, delimiter: ValidDataType) -> List[bitarray]:
    ...


@overload
def partition_bitarray(bitarray_: bitarray, index: int) -> List[bitarray]:
    ...


@overload
def partition_bitarray(bitarray_: bitarray, index: List[int], continous: bool = False) -> List[bitarray]:
    ...


def partition_bitarray(
    bitarray_: bitarray,
    delimiter: Optional[Union[List[Bitcode], Bitcode]] = None,
    index: Optional[Union[List[int], int]] = None,
    continuous: bool = False,
) -> List[bitarray]:
    if (index is None and delimiter is None) or (index != None and delimiter != None):
        raise ValueError("either an index or a delimiter is required")

    if index and not isinstance(index, Iterable):
        return bitarray_[:index], bitarray_[index:]

    if delimiter and not isinstance(delimiter, Iterable):
        index = bitarray_.index(bitarray(delimiter))
        return bitarray_[:index], bitarray_[index:]

    if not index:
        index = []
        index_range = set()
        for sep in delimiter:
            found_indexes = [(ind, len(sep)) for ind in bitarray_.search(bitarray(sep))]

            for i, size in found_indexes:
                found_index_range = range(i, i + size)

                if not index_range.isdisjoint(found_index_range):
                    continue

                index_range.update(found_index_range)
                index.append((i, size))

        index = sorted(index)

    to_process = deque(index)
    # add comment later i forgorr what this thing does
    prev_index = 0
    sections = []

    while to_process:
        curr_index = to_process.popleft()
        left_end = right_start = curr_index

        if delimiter:
            left_end = curr_index[0]
            right_start = curr_index[0] + curr_index[1]

        section_to_append = bitarray_[:left_end]

        if continuous:
            bitarray_ = bitarray_[right_start:]
            prev_index = 0

        sections.append(section_to_append[prev_index:])

        prev_index = right_start

    last_section = bitarray_[prev_index:] if not continuous else bitarray_
    sections.append(last_section)

    return sections
