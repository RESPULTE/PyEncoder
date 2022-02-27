from typing import Type, Dict, Callable
import struct

from pyencoder._type_hints import ValidDataset
from pyencoder.config import BYTEORDER, STRING_ENCODING


def dzigzag(dataset: ValidDataset):
    index_list = generate_dzigzag_index(len(dataset), len(dataset[0]))
    return [dataset[i][j] for (i, j) in index_list]


def idzigzag(dataset: ValidDataset):
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


def vzigzag(dataset: ValidDataset):
    index_list = generate_vzigzag_index(len(dataset), len(dataset[0]))
    return [dataset[i][j] for (i, j) in index_list]


def ivzigzag(dataset: ValidDataset):
    col = row = int(len(dataset) ** 0.5)

    matrix_2D = [[None for _ in range(col)] for _ in range(row)]

    for index, (i, j) in enumerate(generate_vzigzag_index(row, col)):
        matrix_2D[i][j] = dataset[index]

    return matrix_2D


def generate_vzigzag_index(row, col):
    datapacks = []

    for j in range(col):
        insert_index = j * col
        for i in range(row):
            if j % 2 == 0:
                datapacks.append((i, j))
                continue
            datapacks.insert(insert_index, (i, j))

    return datapacks


def hzigzag(dataset: ValidDataset):
    index_list = generate_hzigzag_index(len(dataset), len(dataset[0]))
    return [dataset[i][j] for (i, j) in index_list]


def ihzigzag(dataset: ValidDataset):
    col = row = int(len(dataset) ** 0.5)

    matrix_2D = [[None for _ in range(col)] for _ in range(row)]

    for index, (i, j) in enumerate(generate_hzigzag_index(row, col)):
        matrix_2D[i][j] = dataset[index]

    return matrix_2D


def generate_hzigzag_index(row: int, col: int):
    datapacks = []

    for i in range(row):
        insert_index = i * row
        for j in range(col):
            if i % 2 == 0:
                datapacks.append((i, j))
                continue
            datapacks.insert(insert_index, (i, j))

    return datapacks


def bin2float(b: str):
    endian = ">" if BYTEORDER == "big" else "<"
    h = int(b, 2).to_bytes(8, byteorder=BYTEORDER)
    return struct.unpack(f"{endian}d", h)[0]


def float2bin(f: float, bitlength: int):
    endian = ">" if BYTEORDER == "big" else "<"
    d = struct.unpack(f"{endian}Q", struct.pack(f"{endian}d", f))
    return format(*d, f"0{bitlength}b")


def char2bin(s: str, bitlength: int):
    return format(ord(s), f"0{bitlength}b")


def bin2char(b: str):
    return chr(int(b, 2))


def int2bin(i: int, bitlength: int):
    return format(i, f"0{bitlength}b")


def bin2int(b: str):
    return int(b, 2)


TO_BINARY_CONVERTER: Dict[Type, Callable] = {
    str: char2bin,
    int: int2bin,
    float: float2bin,
}

FROM_BINARY_CONVERTER: Dict[Type, Callable] = {str: bin2char, int: bin2int, float: bin2float}
