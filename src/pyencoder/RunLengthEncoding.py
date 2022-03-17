from typing import Any, List, Tuple, overload

from pyencoder.type_hints import ValidDataset


def encode(dataset: ValidDataset) -> List[Tuple[Any, int]]:
    dataset_size = len(dataset)
    encoded_data = []
    curr_index = 0

    while curr_index < dataset_size:

        curr_elem = dataset[curr_index]
        curr_index += 1
        count = 1

        while curr_index < dataset_size and curr_elem == dataset[curr_index]:
            curr_index += 1
            count += 1

        encoded_data.append((curr_elem, count))

    return encoded_data


def decode(encoded_data: List[Tuple[Any, int]]) -> List[Tuple[Any, int]]:
    decoded_data = []
    for data, count in encoded_data:
        decoded_data.extend([data] * count)
    return decoded_data
