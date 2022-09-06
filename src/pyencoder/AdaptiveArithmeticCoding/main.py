from typing import Dict, Tuple

import pyencoder.config.main_config as main_config
from pyencoder.type_hints import Bitcode, ValidData, ValidDataset

import pyencoder.config.ArithmeticCoding_config as ArithmeticCoding_config
from pyencoder.AdaptiveArithmeticCoding.codebook import AdaptiveArithmeticCodebook


def encode(dataset: ValidDataset) -> Tuple[Dict[ValidData, Tuple[int, int]], Bitcode]:
    codebook = AdaptiveArithmeticCodebook()

    lower_limit = 0
    upper_limit = ArithmeticCoding_config.FULL_RANGE_BITMASK

    index = 0
    end_index = len(dataset)
    encoded_data = ""
    num_pending_bits = 0
    total_symbols = codebook.total_symbols

    while index <= end_index:
        sym = dataset[index] if index < end_index else main_config.EOF_MARKER
        sym_low, sym_high = codebook.catalogue_symbol(sym)

        current_range = upper_limit - lower_limit + 1
        upper_limit = lower_limit + (sym_high * current_range // total_symbols) - 1
        lower_limit = lower_limit + (sym_low * current_range // total_symbols)

        while True:
            if upper_limit < ArithmeticCoding_config.HALF_RANGE:
                encoded_data += "0" + "1" * num_pending_bits
                num_pending_bits = 0

            elif lower_limit >= ArithmeticCoding_config.HALF_RANGE:
                encoded_data += "1" + "0" * num_pending_bits
                num_pending_bits = 0

            elif (
                lower_limit >= ArithmeticCoding_config.QUARTER_RANGE
                and upper_limit < ArithmeticCoding_config.THREE_QUARTER_RANGE
            ):
                lower_limit -= ArithmeticCoding_config.QUARTER_RANGE
                upper_limit -= ArithmeticCoding_config.QUARTER_RANGE
                num_pending_bits += 1

            else:
                break

            lower_limit = lower_limit << 1
            upper_limit = (upper_limit << 1) + 1

            lower_limit &= ArithmeticCoding_config.FULL_RANGE_BITMASK
            upper_limit &= ArithmeticCoding_config.FULL_RANGE_BITMASK

        index += 1

    bit = 0 if lower_limit < ArithmeticCoding_config.QUARTER_RANGE else 1
    encoded_data += f"{bit}{str(bit ^ 1) * (num_pending_bits + 1)}"

    return codebook, encoded_data


def decode(bindata: Bitcode, codebook: AdaptiveArithmeticCodebook) -> ValidDataset:
    lower_limit = 0
    code_values = 0
    upper_limit = ArithmeticCoding_config.FULL_RANGE_BITMASK

    bitstream = iter(bindata)
    for _ in range(ArithmeticCoding_config.PRECISION):
        code_values = (code_values << 1) + int(next(bitstream))

    decoded_data = []
    total_symbols = codebook.total_symbols

    while True:
        current_range = upper_limit - lower_limit + 1
        scaled_code_value = ((code_values - lower_limit + 1) * total_symbols - 1) // current_range

        sym, (sym_low, sym_high) = codebook.probability_symbol_search(scaled_code_value)

        if sym == main_config.EOF_MARKER:
            break

        decoded_data.append(sym)
        upper_limit = lower_limit + (sym_high * current_range // total_symbols) - 1
        lower_limit = lower_limit + (sym_low * current_range // total_symbols)

        while True:

            # value's MSB is 0
            if upper_limit < ArithmeticCoding_config.HALF_RANGE:
                pass

            # value's MSB is 1
            elif lower_limit >= ArithmeticCoding_config.HALF_RANGE:
                lower_limit -= ArithmeticCoding_config.HALF_RANGE
                upper_limit -= ArithmeticCoding_config.HALF_RANGE
                code_values -= ArithmeticCoding_config.HALF_RANGE

            # lower & upper limit are converging
            elif (
                lower_limit >= ArithmeticCoding_config.QUARTER_RANGE
                and upper_limit < ArithmeticCoding_config.THREE_QUARTER_RANGE
            ):
                lower_limit -= ArithmeticCoding_config.QUARTER_RANGE
                upper_limit -= ArithmeticCoding_config.QUARTER_RANGE
                code_values -= ArithmeticCoding_config.QUARTER_RANGE

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
