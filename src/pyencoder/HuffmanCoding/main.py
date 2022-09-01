from heapq import heappop, heappush, heapify
from collections import Counter
from typing import BinaryIO, Literal, Optional, Type, Tuple, Dict, List, overload

from pyencoder.HuffmanCoding.codebook import generate_canonical_codebook

from pyencoder.utils.binary import frombin, frombytes, tobin, tobytes
from pyencoder.type_hints import (
    CorruptedHeaderError,
    CorruptedEncodingError,
    SupportedDataType,
    ValidData,
    ValidDataset,
    Bitcode,
)


# @overload
# def decode(
#     header: Bitcode,
#     encoded_data: Bitcode,
#     dtype: Literal["b", "B", "h", "H", "i", "I", "l", "L", "q", "Q", "f", "d", "s"],
#     length_encoding: bool = False,
# ) -> ValidDataset:
#     ...


# @overload
# def decode(
#     header: Bitcode,
#     encoded_data: Bitcode,
#     dtype: Type[int] | Type[float] | Type[str],
#     length_encoding: bool = False,
# ) -> ValidDataset:
#     ...


def decode(
    codebook: Dict[ValidData, Bitcode],
    encoded_data: Bitcode,
) -> ValidDataset:

    decoded_data = [None] * len(encoded_data)
    to_process = encoded_data
    curr_index = 0
    curr_code = ""

    while to_process:
        curr_code += to_process[:1]
        to_process = to_process[1:]

        if curr_code not in codebook:
            continue

        decoded_data[curr_index] = codebook[curr_code]
        curr_index += 1
        curr_code = ""

    decoded_data = decoded_data[:curr_index]

    return "".join(decoded_data)


def decode_length(
    codebook: Dict[ValidData, Bitcode],
    encoded_data: Bitcode,
    dtype: SupportedDataType,
) -> ValidDataset:

    decoded_data = [None] * len(encoded_data)
    to_process = encoded_data
    curr_index = 0
    curr_code = ""

    if dtype not in ("f", "d", float):
        dtype = int

    while to_process:
        curr_code += to_process[:1]
        to_process = to_process[1:]

        if curr_code not in codebook:
            continue

        curr_elem_binsize = codebook[curr_code]
        curr_elem = frombin(to_process[:curr_elem_binsize], dtype)
        decoded_data[curr_index] = curr_elem

        to_process = to_process[curr_elem_binsize:]
        curr_index += 1
        curr_code = ""

    decoded_data = decoded_data[:curr_index]

    return decoded_data


# @overload
# def encode(
#     dataset: List[float | int],
#     dtype: Literal["b", "B", "h", "H", "i", "I", "l", "L", "q", "Q", "f", "d", "s"],
#     length_encoding: bool = False,
# ):
#     ...


# @overload
# def encode(dataset: List[float | int], dtype: Type[float] | Type[int] | Type[str], length_encoding: bool = False):
#     ...


def encode(
    dataset: ValidDataset, dtype: Optional[SupportedDataType], length_encoding: bool = False
) -> Tuple[Dict[ValidData, Bitcode], Bitcode]:
    codebook = generate_canonical_codebook(dataset)
    encoded_data = "".join([codebook[data] for data in dataset])
    return codebook, encoded_data


def encode_length(
    dataset: ValidDataset, dtype: Optional[SupportedDataType], length_encoding: bool = False
) -> Tuple[Dict[ValidData, Bitcode], Bitcode]:

    if dtype not in ("f", "d", float):
        dtype = int
    bin_dataset = [tobin(data, dtype) for data in dataset]
    binlen_dataset = [len(data) for data in bin_dataset]

    codebook = generate_canonical_codebook(binlen_dataset)
    encoded_data = "".join(
        x for binlen, bindata in zip(binlen_dataset, bin_dataset) for x in (codebook[binlen], bindata)
    )

    return codebook, encoded_data
