from typing import Iterable, Optional, List, Tuple, overload

from pyencoder.type_hints import _T


@overload
def encode(dataset: Iterable[_T]) -> List[Tuple[int, _T]]:
    ...


@overload
def encode(dataset: Iterable[_T], target_value: _T) -> List[Tuple[int, _T]]:
    ...


def encode(dataset: Iterable[_T], target_value: Optional[_T] = None):
    if target_value is not None:
        return targeted_encode(dataset, target_value)
    return general_encode(dataset)


def targeted_encode(dataset: Iterable[_T], target_value: _T) -> List[Tuple[int, str]]:
    dataset_size = len(dataset)
    encoded_data = []
    curr_index = 0

    while curr_index < dataset_size:
        curr_elem = dataset[curr_index]
        curr_index += 1
        count = 1

        if curr_elem != target_value:
            encoded_data.append((0, curr_elem))
            continue

        while curr_index < dataset_size and curr_elem == dataset[curr_index]:
            curr_index += 1
            count += 1

        encoded_data.append((count, dataset[curr_index]))
        curr_index += 1

    return encoded_data


def general_encode(dataset: str) -> List[Tuple[int, _T]]:
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

        encoded_data.append((count, curr_elem))

    return encoded_data
