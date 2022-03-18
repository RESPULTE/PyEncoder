from typing import Any, List, Sequence, Tuple

from pyencoder.type_hints import ValidDataset


def encode(dataset: ValidDataset, target_values: Sequence[Any] = None) -> List[Tuple[Any, int]]:
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

        data_to_extend = [curr_elem, count]
        if target_values is not None and curr_elem not in target_values:
            data_to_extend = [curr_elem] * count

        encoded_data.extend(data_to_extend)

    return encoded_data


# a bit stupid
def decode(encoded_data: List[Tuple[Any, int]]) -> List[Tuple[Any, int]]:
    decoded_data = []

    for data in encoded_data:
        if isinstance(data, tuple):
            data, count = data
            decoded_data.extend([data] * count)
            continue

        decoded_data.append(data)

    return decoded_data
