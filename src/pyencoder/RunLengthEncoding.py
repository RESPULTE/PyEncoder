from typing import Optional, Union, BinaryIO, Dict, Callable

from pyencoder._type_hints import (
    ValidDataType,
    BitCode,
)

from pyencoder.utils import SUPPORTED_RUNTYPE


def encode(dataset: Union[str, list, tuple], dtype: ValidDataType, runtype: Optional[str] = "") -> BitCode:
    dataset_size = len(dataset)
    encoded_data = ""
    curr_index = 0

    while curr_index < dataset_size:

        curr_elem = dataset[curr_index]
        curr_index += 1
        count = 1

        while curr_index < dataset_size and curr_elem == dataset[curr_index]:
            curr_index += 1
            count += 1

        encoded_data += f"{curr_elem}|{count}|"

    return f"{runtype}|{encoded_data}"


def decode(encoded_data: BitCode, dtype: ValidDataType) -> ValidDataType:
    runtype, _, encoded_data = encoded_data.partition("|")
    if runtype != "":
        pass
    encoded_data = encoded_data.split("|")[:-1]
    decoded_data = [dtype(d) for index, data in enumerate(encoded_data) if index % 2 == 0 for d in [data] * int(encoded_data[index + 1])]

    return decoded_data if dtype != str else "".join(decoded_data)
