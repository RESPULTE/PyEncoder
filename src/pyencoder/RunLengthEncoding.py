from typing import Union, BinaryIO, Dict, Callable

from pyencoder._type_hints import (
    DecompressionError,
    ValidDataType,
    BitCode,
    _check_datatype,
    _get_dtype_header,
    SUPPORTED_DTYPE,
    DIV,
)

from pyencoder.utils import SUPPORTED_RUNTYPE


def encode(
    dataset: Union[str, list, tuple], dtype: ValidDataType, runtype: str = None
) -> BitCode:
    _check_datatype(dataset, dtype)

    if runtype is not None:
        if runtype not in SUPPORTED_RUNTYPE:
            raise ValueError(
                f"runtype must be one of supported runtypes: {list(SUPPORTED_RUNTYPE.keys())}"
            )
        dataset = SUPPORTED_RUNTYPE[runtype](dataset)

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

    return encoded_data[:-1]


def decode(encoded_data: BitCode, dtype: ValidDataType) -> ValidDataType:
    encoded_data = encoded_data.split("|")
    decoded_data = [
        dtype(d)
        for index, data in enumerate(encoded_data)
        if index % 2 == 0
        for d in [data] * int(encoded_data[index + 1])
    ]

    return decoded_data if dtype != str else "".join(decoded_data)


def dump(
    dataset: Union[str, list, tuple],
    file: BinaryIO,
    dtype: ValidDataType,
    runtype: str = None,
) -> None:
    runlength_string = encode(dataset, dtype, runtype).encode("utf-8")
    dtype = _get_dtype_header(dtype)

    file.write(dtype + DIV + runlength_string)


def load(file: BinaryIO) -> None:
    try:
        dtype, raw_runlength_string = file.read().split(DIV)
    except:
        raise DecompressionError(
            "Could not read the given file, make sure it has been encoded with the module"
        )

    runlength_string = raw_runlength_string.decode("utf-8")

    return decode(runlength_string, SUPPORTED_DTYPE[dtype])
