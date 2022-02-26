from typing import Dict, Callable

from pyencoder._type_hints import ValidDataset

# fckin inefficient
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


def hzigzag(dataset: ValidDataset):
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
