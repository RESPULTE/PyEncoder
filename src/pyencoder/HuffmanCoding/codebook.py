import operator
import heapq
import collections
from typing import List, NamedTuple, Tuple, Dict

from pyencoder.type_hints import (
    CorruptedHeaderError,
    SupportedDataType,
    ValidData,
    ValidDataset,
    Bitcode,
)


class HuffmanNode(NamedTuple):
    frequency: int
    bitlength: int
    symbols: List[str]

    def __add__(self, other: "HuffmanNode") -> "HuffmanNode":
        return type(self)(
            frequency=self.frequency + other.frequency,
            bitlength=max(self.bitlength, other.bitlength) + 1,
            symbols=self.symbols + other.symbols,
        )


def generate_codebook_from_dataset(dataset: ValidDataset = None) -> Dict[ValidData, Bitcode]:
    # putting the symbol in a list to allow concatenation for 'int' and 'float' during the 'tree building process'
    counted_dataset = collections.Counter(dataset).most_common()

    if len(counted_dataset) == 1:
        return {counted_dataset.pop()[0], 1}

    codebook = {symbol: 0 for symbol, _ in counted_dataset}
    to_process = [HuffmanNode(freq, 1, [symbol]) for symbol, freq in counted_dataset]
    heapq.heapify(to_process)

    while len(to_process) != 1:
        node_1 = heapq.heappop(to_process)
        node_2 = heapq.heappop(to_process)

        new_node = node_1 + node_2
        for sym in new_node.symbols:
            codebook[sym] += 1

        heapq.heappush(to_process, new_node)

    return codebook


def generate_canonical_codebook(dataset: ValidDataset) -> Dict[ValidData, Bitcode]:
    codebook = generate_codebook_from_dataset(dataset)

    # just to ensure that the very first value will be zero
    curr_code = -1
    # making sure that the bit shift won't ever happen for the first value
    prev_bitlength = float("inf")
    # sort the codebook by the bitlength
    to_process = list(codebook.items())
    to_process.sort(key=operator.itemgetter(1))

    canonical_codebook = {}
    for symbol, bitlength in to_process:

        # increment the code, which is in integer form btw, by 1
        # if the bitlength of this symbol is more than the last symbol, left-shift the code using bitwise operation
        curr_code += 1
        if bitlength > prev_bitlength:
            curr_code = curr_code << (bitlength - prev_bitlength)

        canonical_codebook[symbol] = "{0:0{num}b}".format(curr_code, num=bitlength)
        prev_bitlength = bitlength

    return canonical_codebook
