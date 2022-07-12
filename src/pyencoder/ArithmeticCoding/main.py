from bisect import bisect_right
from os import PathLike
from typing import Dict, Iterator, Tuple
from collections import Counter

import pyencoder.ArithmeticCoding.config as config
import pyencoder.config as main_config
from pyencoder.type_hints import ValidDataType, ValidDataset, Bitcode

# load N number of bits at a time
# is an iterable
class BitStream:
    def __init__(self, filepath: PathLike, buffer_size: int = 1) -> None:
        self.filepath = filepath
        self.buffer_size = buffer_size
        self.bit_buffer_size = buffer_size * 8
        self.file_obj = None

    def __enter__(self) -> None:
        self.file_obj = open(self.filepath, "rb")
        return self

    def __iter__(self) -> Iterator:
        cur_byte = int.from_bytes(self.file_obj.read(self.buffer_size), main_config.ENDIAN, signed=False)
        for i in range(1, self.bit_buffer_size + 1, -1):
            yield cur_byte & (1 << i)

    def __exit__(self, exc_type, exc_value, exc_tb) -> None:
        self.file_obj.close()


class ArithmeticCodebook(dict):
    def __init__(self, codebook: Dict[ValidDataType, Tuple[int, int]]) -> None:
        super().__init__(codebook)

        self.__elems, __range = zip(*codebook.items())
        self.__lows, self.__highs = zip(*__range)
        self.total_elems = self.__highs[-1]

        if config.EOF_MARKER not in self:
            self[config.EOF_MARKER] = (self.total_elems, self.total_elems + 1)

    @classmethod
    def from_dataset(cls, dataset: ValidDataset) -> "ArithmeticCodebook":
        cummulative_proabability = 0
        codebook: Dict[ValidDataType, Tuple[int, int]] = {}
        for sym, count in Counter(dataset).most_common():
            sym_lower_limit = cummulative_proabability
            sym_upper_limit = cummulative_proabability + count
            codebook[sym] = (sym_lower_limit, sym_upper_limit)

            cummulative_proabability = sym_upper_limit

        codebook[config.EOF_MARKER] = (cummulative_proabability, cummulative_proabability + 1)

        return cls(codebook)

    def range_search(self, probability: int) -> Tuple[ValidDataType, Tuple[int, int]]:
        index = bisect_right(self.__lows, probability) - 1
        return (self.__elems[index], (self.__lows[index], self.__highs[index]))


def encode(dataset: ValidDataset) -> Tuple[Dict[ValidDataType, Tuple[int, int]], Bitcode]:
    arithmetic_codebook = ArithmeticCodebook.from_dataset(dataset)

    lower_limit = 0
    upper_limit = config.FULL_RANGE_BITMASK

    index = 0
    end_index = len(dataset)
    encoded_data = ""
    num_pending_bits = 0
    total_elems = arithmetic_codebook.total_elems

    while index <= end_index:
        sym = dataset[index] if index < end_index else config.EOF_MARKER
        sym_low, sym_high = arithmetic_codebook[sym]

        current_range = upper_limit - lower_limit + 1
        upper_limit = lower_limit + (sym_high * current_range // total_elems) - 1
        lower_limit = lower_limit + (sym_low * current_range // total_elems)

        while True:
            if upper_limit < config.HALF_RANGE:
                encoded_data += "0" + "1" * num_pending_bits
                num_pending_bits = 0

            elif lower_limit >= config.HALF_RANGE:
                encoded_data += "1" + "0" * num_pending_bits
                num_pending_bits = 0

            elif lower_limit >= config.QUARTER_RANGE and upper_limit < config.THREE_QUARTER_RANGE:
                lower_limit -= config.QUARTER_RANGE
                upper_limit -= config.QUARTER_RANGE
                num_pending_bits += 1

            else:
                break

            lower_limit = lower_limit << 1
            upper_limit = (upper_limit << 1) + 1

            lower_limit &= config.FULL_RANGE_BITMASK
            upper_limit &= config.FULL_RANGE_BITMASK

        index += 1

    bit = 0 if lower_limit < config.QUARTER_RANGE else 1
    encoded_data += f"{bit}{str(bit ^ 1) * (num_pending_bits + 1)}"

    return arithmetic_codebook, encoded_data


def decode(bindata: Bitcode, codebook: Dict[ValidDataType, Tuple[int, int]]) -> ValidDataset:
    arithmetic_codebook = ArithmeticCodebook(codebook)

    lower_limit = 0
    code_values = 0
    upper_limit = config.FULL_RANGE_BITMASK

    bitstream = iter(bindata)
    for _ in range(config.PERCISION):
        code_values = (code_values << 1) + int(next(bitstream))

    decoded_data = []
    total_elems = arithmetic_codebook.total_elems

    while True:
        current_range = upper_limit - lower_limit + 1
        scaled_code_value = ((code_values - lower_limit + 1) * total_elems - 1) // current_range

        sym, (sym_low, sym_high) = arithmetic_codebook.range_search(scaled_code_value)

        if sym == config.EOF_MARKER:
            break

        decoded_data.append(sym)
        upper_limit = lower_limit + (sym_high * current_range // total_elems) - 1
        lower_limit = lower_limit + (sym_low * current_range // total_elems)

        while True:

            # value's MSB is 0
            if upper_limit < config.HALF_RANGE:
                pass

            # value's MSB is 1
            elif lower_limit >= config.HALF_RANGE:
                lower_limit -= config.HALF_RANGE
                upper_limit -= config.HALF_RANGE
                code_values -= config.HALF_RANGE

            # lower & upper limit are converging
            elif lower_limit >= config.QUARTER_RANGE and upper_limit < config.THREE_QUARTER_RANGE:
                lower_limit -= config.QUARTER_RANGE
                upper_limit -= config.QUARTER_RANGE
                code_values -= config.QUARTER_RANGE

            else:
                # lower_limit < 25% AND upper_limit > 75%
                # high & low must be at least 1/4 apart
                break

            lower_limit = lower_limit << 1
            upper_limit = (upper_limit << 1) + 1

            try:
                next_bit = int(next(bitstream))

            except StopIteration:
                next_bit = 0

            code_values = (code_values << 1) + next_bit

    return decoded_data
