from functools import lru_cache
from typing import List, Iterable, Literal, NewType, Tuple, TypeVar, Union, overload

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
