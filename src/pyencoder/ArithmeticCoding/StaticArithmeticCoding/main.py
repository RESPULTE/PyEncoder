from typing import Dict, Iterable, Literal, Tuple

from pyencoder import Settings
from pyencoder.ArithmeticCoding.StaticArithmeticCoding.codebook import StaticArithmeticCodebook

_SAC = Settings.ArithmeticCoding


def encode(data: str) -> Tuple[StaticArithmeticCodebook, str]:
    """

    encodes stirng using StaticArithmeticCoding Algorithm

    Args:
        data (str): string, containing whatever the f you want

    Returns:
        Tuple[StaticArithmeticCodebook, str]: codebook and the encoded data
    """
    data += Settings.EOF_MARKER

    codebook = StaticArithmeticCodebook.from_dataset(data)

    lower_limit = 0
    upper_limit = _SAC.FULL_RANGE_BITMASK

    encoded_data = ""
    num_pending_bits = 0
    total_elems = codebook.total_elems

    for sym in data:
        sym_low, sym_high = codebook[sym]

        current_range = upper_limit - lower_limit + 1
        upper_limit = lower_limit + (sym_high * current_range // total_elems) - 1
        lower_limit = lower_limit + (sym_low * current_range // total_elems)

        while True:
            if upper_limit < _SAC.HALF_RANGE:
                encoded_data += "0" + "1" * num_pending_bits
                num_pending_bits = 0

            elif lower_limit >= _SAC.HALF_RANGE:
                encoded_data += "1" + "0" * num_pending_bits
                num_pending_bits = 0

            elif lower_limit >= _SAC.QUARTER_RANGE and upper_limit < _SAC.THREE_QUARTER_RANGE:
                lower_limit -= _SAC.QUARTER_RANGE
                upper_limit -= _SAC.QUARTER_RANGE
                num_pending_bits += 1

            else:
                break

            lower_limit = lower_limit << 1
            upper_limit = (upper_limit << 1) + 1

            lower_limit &= _SAC.FULL_RANGE_BITMASK
            upper_limit &= _SAC.FULL_RANGE_BITMASK

    bit = 0 if lower_limit < _SAC.QUARTER_RANGE else 1
    encoded_data += f"{bit}{str(bit ^ 1) * (num_pending_bits + 1)}"

    return codebook, encoded_data


def decode(codebook: StaticArithmeticCodebook, encoded_data: str) -> str:
    """
    decodes encoded data using Arithmetic Coding Algorithm

    Args:
        codebook (StaticArithmeticCodebook): codebook, oml you cant be this dum
        encoded_data (str): bitcode, str containing only 0s and 1s

    Returns:
        str: the original dataset (hopefully)
    """

    def iter_bit(__str: str) -> Iterable[Literal[0, 1]]:
        """
        a helper function to return the encoded data bit by bit as integers

        Args:
            __str (str): bitcode, string containing 0s and 1s

        Yields:
            Iterator[Literal[0, 1]]: ...
        """
        i = 0

        try:
            while True:
                yield int(__str[i])
                i += 1

        except IndexError:
            while True:
                yield 0

    lower_limit = 0
    upper_limit = _SAC.FULL_RANGE_BITMASK

    code_values = int(encoded_data[: _SAC.PRECISION], 2)
    bitstream = iter_bit(encoded_data[_SAC.PRECISION :])

    decoded_data = ""
    total_elems = codebook.total_elems

    while True:
        current_range = upper_limit - lower_limit + 1
        scaled_code_value = ((code_values - lower_limit + 1) * total_elems - 1) // current_range

        sym, (sym_low, sym_high) = codebook.search_symbol(scaled_code_value)

        if sym == Settings.EOF_MARKER:
            break

        decoded_data += sym
        upper_limit = lower_limit + (sym_high * current_range // total_elems) - 1
        lower_limit = lower_limit + (sym_low * current_range // total_elems)

        while True:

            # value's MSB is 0
            if upper_limit < _SAC.HALF_RANGE:
                pass

            # value's MSB is 1
            elif lower_limit >= _SAC.HALF_RANGE:
                lower_limit -= _SAC.HALF_RANGE
                upper_limit -= _SAC.HALF_RANGE
                code_values -= _SAC.HALF_RANGE

            # lower & upper limit are converging
            elif lower_limit >= _SAC.QUARTER_RANGE and upper_limit < _SAC.THREE_QUARTER_RANGE:
                lower_limit -= _SAC.QUARTER_RANGE
                upper_limit -= _SAC.QUARTER_RANGE
                code_values -= _SAC.QUARTER_RANGE

            else:
                # lower_limit < 25% AND upper_limit > 75%
                # high & low must be at least 1/4 apart
                break

            lower_limit = lower_limit << 1
            upper_limit = (upper_limit << 1) + 1

            code_values = (code_values << 1) + next(bitstream)

    return decoded_data
