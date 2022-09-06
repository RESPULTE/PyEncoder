from heapq import heappop, heappush, heapify
from collections import Counter

from typing import Tuple, Dict

import pyencoder.config.HuffmanCoding_config as config
from pyencoder.utils.binary import frombin, frombytes, tobin, tobytes
from pyencoder.type_hints import (
    CorruptedHeaderError,
    SupportedDataType,
    ValidData,
    ValidDataset,
    Bitcode,
)


def generate_header_from_codebook(codebook: Dict[ValidData, Bitcode]) -> Tuple[Bitcode, Bitcode]:
    codelengths = ["0" * config.CODELENGTH_BITSIZE for _ in range(config.MAX_CODELENGTH)]
    counted_codelengths = Counter([len(code) for code in codebook.values()])

    for length, count in counted_codelengths.items():
        codelengths[length - 1] = "{0:0{bitlen}b}".format(count, bitlen=config.CODELENGTH_BITSIZE)

    codelengths = "".join(codelengths)
    symbols = "".join(codebook.keys())

    return codelengths, symbols


def generate_codebook_from_dataset(dataset: ValidDataset = None) -> Dict[ValidData, Bitcode]:
    # putting the symbol in a list to allow concatenation for 'int' and 'float' during the 'tree building process'
    counted_dataset = Counter(dataset).most_common()

    # [(frequency, max_bitlength, symbol)]
    to_process = [(count, 1, [symbol]) for symbol, count in counted_dataset]
    codebook = {symbol: 0 for symbol, _ in counted_dataset}

    heapify(to_process)

    while len(to_process) != 1:
        tree_freq_1, tree_max_bitlength_1, tree_1 = heappop(to_process)
        tree_freq_2, tree_max_bitlength_2, tree_2 = heappop(to_process)

        new_subtree = tree_1 + tree_2
        new_subtree_freq = tree_freq_1 + tree_freq_2
        new_subtree_max_bitlength = max(tree_max_bitlength_1, tree_max_bitlength_2) + 1

        for sym in new_subtree:
            codebook[sym] += 1

        # ? wtf is happening here ------------
        balance_factor = 0
        if to_process:
            balance_factor = to_process[0][0]
        # ? -----------------------------------
        heappush(
            to_process,
            (
                new_subtree_freq + balance_factor,
                new_subtree_max_bitlength,
                new_subtree,
            ),
        )

    else:
        if len(codebook) == 1:
            return {k: v + 1 for k, v in codebook.items()}

    return codebook


def generate_canonical_codebook(dataset: ValidDataset) -> Dict[ValidData, Bitcode]:
    codebook = generate_codebook_from_dataset(dataset)

    # just to ensure that the very first value will be zero
    curr_code = -1
    # making sure that the bit shift won't ever happen for the first value
    prev_bitlength = float("inf")
    # sort the codebook by the bitlength
    to_process = sorted([(bitlength, symbol) for symbol, bitlength in codebook.items()])

    canonical_codebook = {}
    for bitlength, symbol in to_process:

        # increment the code, which is in integer form btw, by 1
        # if the bitlength of this symbol is more than the last symbol, left-shift the code using bitwise operation
        curr_code += 1
        if bitlength > prev_bitlength:
            curr_code = curr_code << (bitlength - prev_bitlength)

        canonical_codebook[symbol] = "{0:0{bitlen}b}".format(curr_code, bitlen=bitlength)
        prev_bitlength = bitlength

    return canonical_codebook


# !!!
def generate_codebook_from_header(header: Bitcode, dtype: SupportedDataType) -> Dict[Bitcode, ValidData]:
    try:
        codelength_info = config.CODELENGTH_BITSIZE * config.MAX_CODELENGTH
        bin_codelengths, bin_symbols = header[:codelength_info], header[codelength_info:]

        num_symbols_per_codelength = [
            int(bin_codelengths[bitlen : bitlen + config.CODELENGTH_BITSIZE], 2)
            for bitlen in range(0, len(bin_codelengths), config.CODELENGTH_BITSIZE)
        ]

        num_codelength = len(num_symbols_per_codelength)
        if num_codelength != config.MAX_CODELENGTH:
            raise ValueError(
                f"number of symbols decoded({num_codelength}) does not match the default values({config.MAX_CODELENGTH})"
            )
        symbols = frombin(bin_symbols, dtype, num=sum(num_symbols_per_codelength))
        if not isinstance(symbols, list):
            symbols = [symbols]
    except (IndexError, ValueError) as err:
        raise CorruptedHeaderError("Header cannot be decoded") from err

    codebook = {}
    curr_code = 0
    curr_sym_index = 0

    for bitlength, num in enumerate(num_symbols_per_codelength, start=1):

        for _ in range(num):
            bincode = tobin(curr_code, config.CODELENGTH_DTYPE, bitlength=bitlength)
            codebook[bincode] = symbols[curr_sym_index]
            curr_sym_index += 1
            curr_code += 1

        curr_code = curr_code << 1

    return codebook
