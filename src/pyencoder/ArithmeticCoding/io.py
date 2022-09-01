from typing import BinaryIO, TextIO

import pyencoder.config as main_config
import pyencoder.ArithmeticCoding.config as config

from pyencoder.utils.BitIO import BufferedBitInput, BufferedBitOutput
from pyencoder.ArithmeticCoding.codebook import AdaptiveArithmeticCodebook


def load(input_file: TextIO, output_file: BinaryIO = None) -> None:
    codebook = AdaptiveArithmeticCodebook()

    lower_limit = 0
    code_values = 0
    upper_limit = config.FULL_RANGE_BITMASK

    bitstream = BufferedBitInput(input_file, config.PRECISION // 8, as_int=True)

    for i in range(config.PRECISION):
        code_values = (code_values << 1) + i

    while True:
        current_range = upper_limit - lower_limit + 1
        scaled_code_value = ((code_values - lower_limit + 1) * codebook.total_symbols - 1) // current_range

        sym = codebook.get_symbol(scaled_code_value)
        sym_low, sym_high = codebook.get_probability(sym)

        if sym == main_config.EOF_MARKER:
            break

        output_file.write(sym)
        upper_limit = lower_limit + ((sym_high * current_range) // codebook.total_symbols) - 1
        lower_limit = lower_limit + ((sym_low * current_range) // codebook.total_symbols)
        codebook[sym] += 1

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

            code_values = (code_values << 1) + bitstream.read()


def dump(input_file: TextIO, output_file: BinaryIO) -> None:
    codebook = AdaptiveArithmeticCodebook()
    output_bitstream = BufferedBitOutput(output_file, config.PRECISION // 8)

    lower_limit = 0
    upper_limit = config.FULL_RANGE_BITMASK

    encoding = True
    num_pending_bits = 0

    while encoding:

        sym = input_file.read(1)

        if not sym:
            sym = main_config.EOF_MARKER
            encoding = False

        sym_low, sym_high = codebook.get_probability(sym)

        current_range = upper_limit - lower_limit + 1
        upper_limit = lower_limit + ((sym_high * current_range) // codebook.total_symbols) - 1
        lower_limit = lower_limit + ((sym_low * current_range) // codebook.total_symbols)
        codebook[sym] += 1

        while True:
            if upper_limit < config.HALF_RANGE:
                output_bitstream.write("0" + "1" * num_pending_bits)
                num_pending_bits = 0

            elif lower_limit >= config.HALF_RANGE:
                output_bitstream.write("1" + "0" * num_pending_bits)
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

    num_pending_bits += 1
    bit = 0 if lower_limit < config.QUARTER_RANGE else 1
    output_bitstream.write("%s%s" % (bit, str(bit ^ 1) * num_pending_bits))
    output_bitstream.flush()
