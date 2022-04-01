from typing import Optional, List, Tuple, overload

from pyencoder.type_hints import ValidDataset, T


@overload
def encode(dataset: ValidDataset) -> List[Tuple[int, T]]:
    ...


@overload
def encode(dataset: ValidDataset, target_value: T, end_marker: T = (0, 0)) -> List[Tuple[int, T]]:
    ...


def encode(dataset: ValidDataset, target_value: Optional[T] = None, end_marker: Optional[T] = (0, 0)):
    if target_value is not None:
        return targeted_encode(dataset, target_value, end_marker)
    return general_encode(dataset)


def targeted_encode(dataset: ValidDataset, target_value: T, end_marker: T) -> List[Tuple[int, T]]:
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

        if curr_index == dataset_size:
            encoded_data.append(end_marker)
            break

        encoded_data.append((count, dataset[curr_index]))
        curr_index += 1

    return encoded_data


def general_encode(dataset: ValidDataset) -> List[Tuple[int, T]]:
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
