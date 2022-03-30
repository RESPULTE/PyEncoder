from decimal import Decimal, getcontext
from collections import Counter
from typing import BinaryIO, Optional, Tuple, Dict

from pyencoder import config
from pyencoder.utils.binary import tobin, frombin, Bitstring
from pyencoder.type_hints import (
    CorruptedHeaderError,
    CorruptedEncodingError,
    SupportedDataType,
    ValidDataType,
    ValidDataset,
    Bitcode,
)

# refer to nayuki's project for guidance
def encode(dataset: ValidDataset) -> Tuple[Dict[ValidDataType, Tuple[Decimal, Decimal]], Bitcode]:
    codebook = _generate_codebook_from_dataset(dataset)

    start = Decimal(0)
    delta = Decimal(1)

    for sym in dataset:
        sym_start, sym_delta = codebook[sym]
        start += delta * sym_start
        delta *= sym_delta

    return codebook, start


def decode(
    codebook: Dict[Tuple[Decimal, Decimal], ValidDataType],
    encoded_data: float,
    dtype: SupportedDataType,
) -> ValidDataset:
    start = Decimal(0)
    delta = Decimal(1)
    decoded_data = []

    while start != encoded_data:

        for (sym_start, sym_delta), sym in codebook.items():
            new_start = start + (delta * sym_start)
            new_delta = delta * sym_delta

            if not (new_start < encoded_data < new_start + new_delta) and new_start != encoded_data:
                continue

            decoded_data.append(sym)

            start, delta = new_start, new_delta
            if start == encoded_data:
                break

    if dtype == "s":
        decoded_data = "".join(decoded_data)

    return decoded_data


def dump(dataset: ValidDataset, dtype: SupportedDataType, file: BinaryIO) -> None:
    pass


def load(file: BinaryIO, dtype: SupportedDataType) -> ValidDataset:
    pass


def _generate_codebook_from_dataset(dataset: ValidDataset) -> Dict[ValidDataType, Tuple[Decimal, Decimal]]:
    to_process = Counter(dataset).most_common()

    start = Decimal(0)
    codebook = {}
    dataset_size = Decimal(len(dataset))
    for symbol, count in to_process:
        delta = count / dataset_size
        codebook[symbol] = (start, delta)
        start += delta

    return codebook


# def generate_codebook_from_header(
#     header: Bitcode, dtype: SupportedDataType
# ) -> Dict[ValidDataType, Tuple[Decimal, Decimal]]:
#     while header:

#         symbol = header[:8]


# def generate_header_from_codebook(
#     codebook: Dict[ValidDataType, Tuple[Decimal, Decimal]], dtype: SupportedDataType
# ) -> Bitcode:
#     probabilities = ["0" * config.CODELENGTH_BITSIZE for _ in range(0, config.MAX_CODELENGTH)]

#     for sym, prob in codebook.items():
#         probabilities[length - 1] = tobin(
#             data=count, bitlength=config.CODELENGTH_BITSIZE, dtype=config.CODELENGTH_DTYPE
#         )

#     probabilities = "".join(probabilities)
#     symbols = tobin(list(codebook.keys()), dtype=dtype)

#     return probabilities, symbols

# getcontext().prec = 5
# s = "Never gonna give you up" * 10
# cb, ed = encode(s)
# cb = {v: k for k, v in cb.items()}
# print(decode(cb, ed, "s"))
