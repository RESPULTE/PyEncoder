from collections import Counter, namedtuple
from typing import Dict

from pyencoder.type_hints import ValidDataType, ValidDataset, Bitcode

SymbolProbabilityRange = namedtuple("SymbolProbabilityRange", ["lower_limit", "upper_limit"])


class ArithmeticCodeRange:
    def __init__(self, percision: int) -> None:
        self.full_range = 1 << percision
        self.half_range = self.full_range >> 1
        self.quarter_range = self.half_range >> 1

        self.min_range = self.quarter_range >> 1 + 2
        # Bit mask of num_state_bits ones, which is 0111...111.
        self.bit_mask = self.full_range - 1

        # ---mutable attribute---
        # Low end of this arithmetic coder's current range. Conceptually has an infinite number of trailing 0s.
        self.lower_limit = 0
        # High end of this arithmetic coder's current range. Conceptually has an infinite number of trailing 1s.
        self.upper_limit = self.bit_mask

    def __post_init__(self) -> None:
        # if lower_limit >= upper_limit or (lower_limit & lookup_table.bit_mask) != lower_limit or (upper_limit & lookup_table.bit_mask) != upper_limit:
        #     raise AssertionError("Low or upper_limit out of range")

        # if not (lookup_table.min_range <= lookup_table.range <= lookup_table.full_range):
        #     raise AssertionError("Range out of range")
        pass

    @property
    def range(self) -> float:
        return self.upper_limit - self.lower_limit + 1


def generate_probability_table(dataset: ValidDataset) -> Dict[ValidDataType, SymbolProbabilityRange]:
    frequency_table: Dict[str, SymbolProbabilityRange] = {}
    cummulative_proabability = 0
    for sym, count in Counter(dataset).most_common():
        sym_lower_limit = cummulative_proabability
        sym_upper_limit = cummulative_proabability + count
        frequency_table[sym] = SymbolProbabilityRange(sym_lower_limit, sym_upper_limit)

        cummulative_proabability = sym_upper_limit

    return frequency_table


def encode(dataset: ValidDataset, percision: int = 32) -> Bitcode:
    frequency_table = generate_probability_table(dataset)
    range_table = ArithmeticCodeRange(percision)
    total_elem = len(dataset)
    encoded_data = []

    for sym in dataset:
        sym_prob = frequency_table[sym]

        range_table.upper_limit = range_table.lower_limit + (sym_prob.upper_limit * range_table.range // total_elem) - 1
        range_table.lower_limit = range_table.lower_limit + (sym_prob.lower_limit * range_table.range // total_elem)

        # While low and high have the same top bit value, shift them out
        while ((range_table.lower_limit ^ range_table.upper_limit) & range_table.half_range) == 0:
            range_table.shift()
            range_table.lower_limit = (range_table.lower_limit << 1) & range_table.bit_mask
            range_table.upper_limit = ((range_table.upper_limit << 1) & range_table.bit_mask) | 1

        # Now low's top bit must be 0 and high's top bit must be 1

        # While low's top two bits are 01 and high's are 10, delete the second highest bit of both
        while (range_table.lower_limit & ~range_table.upper_limit & range_table.quarter_range) != 0:
            range_table.underflow()
            range_table.lower_limit = (range_table.lower_limit << 1) ^ range_table.half_range
            range_table.upper_limit = (
                ((range_table.upper_limit ^ range_table.half_range) << 1) | range_table.half_range | 1
            )
