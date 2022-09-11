from typing import Tuple, Dict

from pyencoder import Settings
from pyencoder.utils.bitbuffer import BitStringBuffer
from pyencoder.HuffmanCoding.StaticHuffmanCoding.codebook import generate_canonical_codebook


def decode(codebook: Dict[str, str], encoded_data: str) -> str:
    codebook = {v: k for k, v in codebook.items()}
    decoded_data = ""
    curr_code = ""

    to_process = BitStringBuffer(encoded_data)
    while to_process:
        curr_code += to_process.read(1)

        if curr_code not in codebook:
            continue

        symbol = codebook[curr_code]
        if symbol == Settings.EOF_MARKER:
            break

        decoded_data += symbol
        curr_code = ""

    return decoded_data


def encode(data: str) -> Tuple[Dict[str, str], str]:
    codebook = generate_canonical_codebook(data)
    encoded_data = "".join([codebook[data] for data in data])
    return codebook, encoded_data
