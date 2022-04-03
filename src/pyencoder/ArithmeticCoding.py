from collections import Counter
from typing import Dict, Tuple

from pyencoder.type_hints import ValidDataType, ValidDataset, Bitcode
from pyencoder.utils.binary import tobin


class ArithmeticCoderLookUp:
    def __init__(self, percision: int, total_elem: int) -> None:
        self.percision = percision
        self.total_elem = total_elem

        # --- constant attributes --- #
        self.full_range = 1 << self.percision
        self.half_range = self.full_range >> 1
        self.quarter_range = self.half_range >> 1

        # --- state attributes --- #
        self.underflowed_bits = 0
        self.lower_limit = 0  # (Conceptually) contains infinite number of trailing 0s.
        self.upper_limit = self.bit_mask  # (Conceptually) contains infinite number of trailing 1s.

        # --- helper attributes --- #
        self.min_range = self.quarter_range >> 1 + 2  # used for error checking
        self.shift_range = (
            self.percision - 1
        )  # used for determining the number of values to shift to get the most significant bit
        self.bit_mask = self.full_range - 1  # used for getting rid of most significant bit in the updating process

    def __post_init__(self) -> None:
        # if lower_limit >= upper_limit or (lower_limit & lookup_table.bit_mask) != lower_limit or (upper_limit & lookup_table.bit_mask) != upper_limit:
        #     raise AssertionError("Low or upper_limit out of range")

        # if not (lookup_table.min_range <= lookup_table.range <= lookup_table.full_range):
        #     raise AssertionError("Range out of range")
        pass

    @property
    def range(self) -> int:
        return self.upper_limit - self.lower_limit + 1

    def update(self, new_lower_limit: int, new_upper_limit: int) -> str:
        self.update_limit(new_lower_limit, new_upper_limit)
        output_bits = self.output()
        self.recalibrate_range()
        return output_bits

    def update_limit(self, new_lower_limit: int, new_upper_limit: int) -> None:
        """
        increase the lower limit or decrease the upper limit bsaed on the symbols probability range

        Args:
            new_lower_limit (int): symbol's probability's lower limit
            new_upper_limit (int): symbol's probability's upper limit
        """
        self.upper_limit = self.lower_limit + (new_upper_limit * self.range // self.total_elem) - 1
        self.lower_limit = self.lower_limit + (new_lower_limit * self.range // self.total_elem)

    def shift(self) -> Bitcode:
        """
        shift out the lower_limit's most significant bit, plus any accumulated underflowed bits,
        which will be the opposite of the said bit.

        Returns:
            str: combined value of lower_limit's most significant bit and underflowed bits
        """
        bit = self.lower_limit >> self.shift_range
        underflowed_bits = str(bit ^ 1) * self.underflowed_bits

        self.underflowed_bits = 0
        return "%s%s" % (bit, underflowed_bits)

    def output(self) -> Bitcode:
        """
        check the most significant bit of both limits to see whether the most significant bit
        of the 2 limits are the same, i.e 'convergence' has happened.
        If so, 'shift out' the most significant bit and return it.

        * This will keep the range of int values from expanding out of bound,
        * Plus, no point in keeping the most significant bits when it's the same for both limits.
        * P.S: After this, the most significant bit for the upper limit must be 1, while the lower limit must be 0

        Returns:
            Bitcode: combined value of lower_limit's most significant bit and underflowed bits
        """
        # 1. 'XOR' upper & lower limit:
        #   - if the most significant bit are the same, the resulting value will have 0 as the most significant bit
        #
        # 2. 'AND' with the half_range:
        #   - if the resulting value has 0 as the most significant bit, the resulting resulting value will to be 0
        #   * essentially, checking whether the most significant bit of the resulting value from 'XOR' is 0
        retval = ""
        while ((self.lower_limit ^ self.upper_limit) & self.half_range) == 0:
            retval += self.shift()

            # left-shifting the limits, then apply bitwise "AND" with the bit_mask
            # * essentially, getting rid of the most significant bit
            self.lower_limit = (self.lower_limit << 1) & self.bit_mask
            self.upper_limit = ((self.upper_limit << 1) & self.bit_mask) | 1

        return retval

    def recalibrate_range(self) -> None:
        """
        check the next most significant bit of both limits to see whether 'near-convergence' will be happening
        - Avoid the 2 limits from converging on the value 0.5
          -> when the upper limit approaches '10000000000...'
          -> when the lower limit approached '01111111111...'

          -> The numbers are getting closer and closer together,
             but because neither has crossed over the 0.5 divider,
             no bits are getting shifted out.

          -> when the range has value of just 1, subdividing the range [0,1]
             will just give the same result for any symbols

        near-convergence: upper_limit has '10' as the most significant bit
                          lower_limit has '01' as the most significant bit
                          -> range between both limit is about 0.25

        """
        # --- While top 2 bits of lower_limit and upper_limit are '01' and '10' ---
        # 1. Second most significant bit is deleted
        # 2. The all bits after the first bit are left-shifted by 1
        # 3. '0' is shifted in as lower limit's least significant bit
        #    '1' is shifted in as upper limit's least significant bit
        # 4. increment the counter for the underflowed bits
        while (self.lower_limit & ~self.upper_limit & self.quarter_range) != 0:
            self.underflowed_bits += 1
            self.lower_limit = (self.lower_limit << 1) ^ self.half_range
            self.upper_limit = ((self.upper_limit ^ self.half_range) << 1) | self.half_range | 1


def generate_probability_table(dataset: ValidDataset) -> Dict[ValidDataType, Tuple[int, int]]:
    """
    generate a dictionary of upper & lower range of probability
    based on the frequncy of occurence of all the unique symbols in the dataset

    Args:
        dataset (ValidDataset): an Itreable containing data of any kind

    Returns:
        Dict[ValidDataType, Tuple[int, int]]:
        - a dictionary containing the unique symbols as the key and the symbol's probability range
          upper/lower limit as the values
    """
    frequency_table: Dict[str, Tuple[int, int]] = {}
    cummulative_proabability = 0
    for sym, count in Counter(dataset).most_common():
        sym_lower_limit = cummulative_proabability
        sym_upper_limit = cummulative_proabability + count
        frequency_table[sym] = (sym_lower_limit, sym_upper_limit)

        cummulative_proabability = sym_upper_limit

    return frequency_table


def encode(dataset: ValidDataset, percision: int = 32) -> Bitcode:
    frequency_table = generate_probability_table(dataset)
    range_table = ArithmeticCoderLookUp(percision, len(dataset))
    encoded_data = ""

    for sym in dataset:
        sym_prob = frequency_table[sym]
        encoded_data += range_table.update(*sym_prob)

    return frequency_table, encoded_data


# def get_bounded_symbol(VALUE) -> Any:
#     while end - start > 1:
#         middle = (start + end) >> 1
#         if freqs.get_low(middle) > value:
#             end = middle
#         else:
#             start = middle

# def decode(
#     codebook: Dict[ValidDataType, Bitcode],
#     encoded_data: Bitcode,
#     dtype: SupportedDataType,
#     length_encoding: bool = False,
# ) -> ValidDataset:
#     PASS
# print(encode("1294jfrioqevqer3rw21"))

