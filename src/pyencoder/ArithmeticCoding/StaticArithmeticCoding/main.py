from typing import Dict, Tuple

from pyencoder.utils.BitIO import BufferedBitInput
from pyencoder.ArithmeticCoding import Settings
from pyencoder import Config

from pyencoder.ArithmeticCoding.StaticArithmeticCoding.codebook import ArithmeticCodebook


def encode(dataset: str) -> Tuple[Dict[str, Tuple[int, int]], str]:
    dataset += Config["EOF_MARKER"]

    codebook = ArithmeticCodebook.from_dataset(dataset)

    lower_limit = 0
    upper_limit = Settings.FULL_RANGE_BITMASK

    encoded_data = ""
    num_pending_bits = 0
    total_elems = codebook.total_elems

    for sym in dataset:
        sym_low, sym_high = codebook[sym]

        current_range = upper_limit - lower_limit + 1
        upper_limit = lower_limit + (sym_high * current_range // total_elems) - 1
        lower_limit = lower_limit + (sym_low * current_range // total_elems)

        while True:
            if upper_limit < Settings.HALF_RANGE:
                encoded_data += "0" + "1" * num_pending_bits
                num_pending_bits = 0

            elif lower_limit >= Settings.HALF_RANGE:
                encoded_data += "1" + "0" * num_pending_bits
                num_pending_bits = 0

            elif lower_limit >= Settings.QUARTER_RANGE and upper_limit < Settings.THREE_QUARTER_RANGE:
                lower_limit -= Settings.QUARTER_RANGE
                upper_limit -= Settings.QUARTER_RANGE
                num_pending_bits += 1

            else:
                break

            lower_limit = lower_limit << 1
            upper_limit = (upper_limit << 1) + 1

            lower_limit &= Settings.FULL_RANGE_BITMASK
            upper_limit &= Settings.FULL_RANGE_BITMASK

    bit = 0 if lower_limit < Settings.QUARTER_RANGE else 1
    encoded_data += f"{bit}{str(bit ^ 1) * (num_pending_bits + 1)}"

    return codebook, encoded_data


def decode(bindata: str, codebook: ArithmeticCodebook) -> str:
    lower_limit = 0
    upper_limit = Settings.FULL_RANGE_BITMASK

    bitstream = BufferedBitInput(bindata, as_int=True, default_value=0)
    code_values = bitstream.read(Settings.PRECISION)

    decoded_data = []
    total_elems = codebook.total_elems

    while True:
        current_range = upper_limit - lower_limit + 1
        scaled_code_value = ((code_values - lower_limit + 1) * total_elems - 1) // current_range

        sym, (sym_low, sym_high) = codebook.search_symbol(scaled_code_value)

        if sym == Config["EOF_MARKER"]:
            break

        decoded_data.append(sym)
        upper_limit = lower_limit + (sym_high * current_range // total_elems) - 1
        lower_limit = lower_limit + (sym_low * current_range // total_elems)

        while True:

            # value's MSB is 0
            if upper_limit < Settings.HALF_RANGE:
                pass

            # value's MSB is 1
            elif lower_limit >= Settings.HALF_RANGE:
                lower_limit -= Settings.HALF_RANGE
                upper_limit -= Settings.HALF_RANGE
                code_values -= Settings.HALF_RANGE

            # lower & upper limit are converging
            elif lower_limit >= Settings.QUARTER_RANGE and upper_limit < Settings.THREE_QUARTER_RANGE:
                lower_limit -= Settings.QUARTER_RANGE
                upper_limit -= Settings.QUARTER_RANGE
                code_values -= Settings.QUARTER_RANGE

            else:
                # lower_limit < 25% AND upper_limit > 75%
                # high & low must be at least 1/4 apart
                break

            lower_limit = lower_limit << 1
            upper_limit = (upper_limit << 1) + 1
            code_values = (code_values << 1) + bitstream.read(1)

    return decoded_data
