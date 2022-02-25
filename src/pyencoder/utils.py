from typing import Dict, Callable

from pyencoder._type_hints import ValidDataset

# fckin inefficient
def _diagonal_zigzag_traversal(dataset: ValidDataset):
    row, col = len(dataset), len(dataset[0])
    datapacks = [[] for i in range(row + col - 1)]

    for i in range(row):
        for j in range(col):
            index_sum = i + j
            data = dataset[i][j]
            if index_sum % 2 == 0:
                datapacks[index_sum].insert(0, data)
                continue
            datapacks[index_sum].append(data)

    return [data for packet in datapacks for data in packet]


def _inverse_diagonal_zigzag_traversal(dataset: ValidDataset):
    pass


def _vertical_zigzag_traversal(dataset: ValidDataset):
    row, col = len(dataset), len(dataset[0])
    datapacks = []

    for j in range(col):
        insert_index = j * col
        for i in range(row):
            data = dataset[i][j]
            if j % 2 == 0:
                datapacks.append(data)
                continue
            datapacks.insert(insert_index, data)

    return datapacks


def _inverse_vertical_zigzag_traversal(dataset: ValidDataset):
    pass


def _horizontal_zigzag_traversal(dataset: ValidDataset):
    row, col = len(dataset), len(dataset[0])
    datapacks = []

    for i in range(row):
        insert_index = i * row
        for j in range(col):
            data = dataset[i][j]
            if i % 2 == 0:
                datapacks.append(data)
                continue
            datapacks.insert(insert_index, data)

    return datapacks


def _inverse_horizontal_zigzag_traversal(dataset: ValidDataset):
    pass


SUPPORTED_RUNTYPE: Dict[str, Callable] = {
    "vz": _vertical_zigzag_traversal,
    "hz": _horizontal_zigzag_traversal,
    "dz": _diagonal_zigzag_traversal,
}


def triangular(n):
    return n * (n + 1) // 2


print(_inverse_diagonal_zigzag_traversal(_diagonal_zigzag_traversal([[1, 2, 3], [4, 5, 6], [7, 8, 9]])))
