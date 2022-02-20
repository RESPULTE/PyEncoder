from typing import Dict, Callable

from pyencoder._type_hints import ValidDataset


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

SUPPORTED_RUNTYPE: Dict[str, Callable] = {
    "v-zigzag": _vertical_zigzag_traversal,
    "h-zigzag": _horizontal_zigzag_traversal,
    "d-zigzag": _diagonal_zigzag_traversal,
}