from heapq import heappop, heappush, heapify
from collections import Counter
from typing import BinaryIO, Literal, Optional, Type, Tuple, Dict, List, overload

from pyencoder.HuffmanCoding.codebook import generate_canonical_codebook
import pyencoder.config.HuffmanCoding_config as config
from pyencoder.utils.BitIO import BufferedBitInput
from pyencoder.type_hints import (
    CorruptedHeaderError,
    CorruptedEncodingError,
    SupportedDataType,
    ValidData,
    ValidDataset,
    Bitcode,
)


def decode(
    codebook: Dict[ValidData, Bitcode],
    encoded_data: Bitcode,
) -> ValidDataset:

    decoded_data = ""
    curr_code = ""

    to_process = BufferedBitInput(encoded_data)
    while to_process:
        curr_code += to_process.read(1)

        if curr_code not in codebook:
            continue

        symbol = codebook[curr_code]
        if symbol == config.EOF_MARKER:
            break

        decoded_data += symbol
        curr_code = ""

    return decoded_data


def encode(dataset: ValidDataset) -> Tuple[Dict[ValidData, Bitcode], Bitcode]:
    codebook = generate_canonical_codebook(dataset)
    encoded_data = "".join([codebook[data] for data in dataset])
    return codebook, encoded_data
