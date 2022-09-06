from typing import Dict, Generator, Iterable, Tuple


import pyencoder.config.main_config as main_config
import pyencoder.config.ArithmeticCoding_config as ArithmeticCoding_config

from pyencoder.AdaptiveArithmeticCoding.codebook import AdaptiveArithmeticCodebook
from pyencoder.utils.BitIO import BufferedBitInput
from pyencoder.type_hints import Bitcode


class AdaptiveArithmeticEncoder:
    def __init__(self):
        self.lower_limit = 0
        self.upper_limit = ArithmeticCoding_config.FULL_RANGE_BITMASK
        self.num_pending_bits = 0

        self.codebook = AdaptiveArithmeticCodebook()

        self.encoder = self._encode()
        self.encoder.send(None)

    def encode(self, symbol: str) -> Bitcode:
        return self.encoder.send(symbol)

    def _encode(self) -> Generator[Bitcode, str, None]:
        code = ""

        while True:
            sym = yield code

            code = ""
            total_symbols = self.codebook.total_symbols
            sym_low, sym_high = self.codebook.catalogue_symbol(sym)

            current_range = self.upper_limit - self.lower_limit + 1
            self.upper_limit = self.lower_limit + (sym_high * current_range // total_symbols) - 1
            self.lower_limit = self.lower_limit + (sym_low * current_range // total_symbols)

            while True:
                if self.upper_limit < ArithmeticCoding_config.HALF_RANGE:
                    code += "0" + "1" * self.num_pending_bits
                    self.num_pending_bits = 0

                elif self.lower_limit >= ArithmeticCoding_config.HALF_RANGE:
                    code += "1" + "0" * self.num_pending_bits
                    self.num_pending_bits = 0

                elif (
                    self.lower_limit >= ArithmeticCoding_config.QUARTER_RANGE
                    and self.upper_limit < ArithmeticCoding_config.THREE_QUARTER_RANGE
                ):
                    self.lower_limit -= ArithmeticCoding_config.QUARTER_RANGE
                    self.upper_limit -= ArithmeticCoding_config.QUARTER_RANGE
                    self.num_pending_bits += 1

                else:
                    break

                self.lower_limit = self.lower_limit << 1
                self.upper_limit = (self.upper_limit << 1) + 1

                self.lower_limit &= ArithmeticCoding_config.FULL_RANGE_BITMASK
                self.upper_limit &= ArithmeticCoding_config.FULL_RANGE_BITMASK

    def flush(self) -> Bitcode:
        code = self.encoder.send(main_config.EOF_MARKER)

        self.num_pending_bits += 1
        bit = 0 if self.lower_limit < ArithmeticCoding_config.QUARTER_RANGE else 1
        return code + f"{bit}{str(bit ^ 1) * (self.num_pending_bits + 1)}"


encoder = AdaptiveArithmeticEncoder()
encode = encoder.encode
flush = encoder.flush


class AdaptiveArithmeticDecoder:
    def __init__(self) -> None:
        self.lower_limit = 0
        self.upper_limit = ArithmeticCoding_config.FULL_RANGE_BITMASK
        self.code_values = 0

        self.codebook = AdaptiveArithmeticCodebook()

    def decode(self, bindata: Bitcode) -> Iterable[str]:
        bitstream = BufferedBitInput(bindata, ArithmeticCoding_config.PRECISION // 8, as_int=True)

        for _ in range(ArithmeticCoding_config.PRECISION):
            self.code_values = (self.code_values << 1) + bitstream.read(1)

        while True:
            current_range = self.upper_limit - self.lower_limit + 1
            total_symbols = self.codebook.total_symbols

            scaled_code_value = ((self.code_values - self.lower_limit + 1) * total_symbols - 1) // current_range

            sym, (sym_low, sym_high) = self.codebook.probability_symbol_search(scaled_code_value)

            if sym == main_config.EOF_MARKER:
                break

            yield sym
            self.upper_limit = self.lower_limit + (sym_high * current_range // total_symbols) - 1
            self.lower_limit = self.lower_limit + (sym_low * current_range // total_symbols)

            while True:

                # value's MSB is 0
                if self.upper_limit < ArithmeticCoding_config.HALF_RANGE:
                    pass

                # value's MSB is 1
                elif self.lower_limit >= ArithmeticCoding_config.HALF_RANGE:
                    self.lower_limit -= ArithmeticCoding_config.HALF_RANGE
                    self.upper_limit -= ArithmeticCoding_config.HALF_RANGE
                    self.code_values -= ArithmeticCoding_config.HALF_RANGE

                # lower & upper limit are converging
                elif (
                    self.lower_limit >= ArithmeticCoding_config.QUARTER_RANGE
                    and self.upper_limit < ArithmeticCoding_config.THREE_QUARTER_RANGE
                ):
                    self.lower_limit -= ArithmeticCoding_config.QUARTER_RANGE
                    self.upper_limit -= ArithmeticCoding_config.QUARTER_RANGE
                    self.code_values -= ArithmeticCoding_config.QUARTER_RANGE

                else:
                    # self.lower_limit < 25% AND self.upper_limit > 75%
                    # high & low must be at least 1/4 apart
                    break

                self.lower_limit = self.lower_limit << 1
                self.upper_limit = (self.upper_limit << 1) + 1
                self.code_values = (self.code_values << 1) + (bitstream.read(1) or 0)


decode = AdaptiveArithmeticDecoder().decode
