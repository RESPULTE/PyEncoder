from typing import Tuple, Dict

from pyencoder import Config
from pyencoder.utils.BitIO import BufferedBitInput
from pyencoder.HuffmanCoding.StaticHuffmanCoding.codebook import generate_canonical_codebook


def decode(codebook: Dict[str, str], encoded_data: str) -> str:

    decoded_data = ""
    curr_code = ""

    to_process = BufferedBitInput(encoded_data)
    while to_process:
        curr_code += to_process.read(1)

        if curr_code not in codebook:
            continue

        symbol = codebook[curr_code]
        if symbol == Config["EOF_MARKER"]:
            break

        decoded_data += symbol
        curr_code = ""

    return decoded_data


def encode(dataset: str) -> Tuple[Dict[str, str], str]:
    codebook = generate_canonical_codebook(dataset)
    encoded_data = "".join([codebook[data] for data in dataset])
    return codebook, encoded_data
