from typing import Generator

from pyencoder import Settings
from pyencoder.utils.bitbuffer import BitIntegerBuffer
from pyencoder.utils.misc import check_is_symbol

from pyencoder.ArithmeticCoding.AdaptiveArithmeticCoding.codebook import AdaptiveArithmeticCodebook

_SAC = Settings.ArithmeticCoding


class AdaptiveEncoder:
    def __init__(self):
        self.lower_limit = 0
        self.upper_limit = _SAC.FULL_RANGE_BITMASK
        self.num_pending_bits = 0

        self.codebook = AdaptiveArithmeticCodebook()

        self.encoder = self._encode()
        self.encoder.send(None)

    def encode(self, symbol: str) -> str:
        check_is_symbol(symbol)
        return self.encoder.send(symbol)

    def _encode(self) -> Generator[str, str, None]:
        code = ""

        while True:
            sym = yield code

            code = ""
            total_symbols = self.codebook.symbol_counts
            sym_low, sym_high = self.codebook.catalogue_symbol(sym)

            current_range = self.upper_limit - self.lower_limit + 1
            self.upper_limit = self.lower_limit + (sym_high * current_range // total_symbols) - 1
            self.lower_limit = self.lower_limit + (sym_low * current_range // total_symbols)

            while True:
                if self.upper_limit < _SAC.HALF_RANGE:
                    code += "0" + "1" * self.num_pending_bits
                    self.num_pending_bits = 0

                elif self.lower_limit >= _SAC.HALF_RANGE:
                    code += "1" + "0" * self.num_pending_bits
                    self.num_pending_bits = 0

                elif self.lower_limit >= _SAC.QUARTER_RANGE and self.upper_limit < _SAC.THREE_QUARTER_RANGE:
                    self.lower_limit -= _SAC.QUARTER_RANGE
                    self.upper_limit -= _SAC.QUARTER_RANGE
                    self.num_pending_bits += 1

                else:
                    break

                self.lower_limit = self.lower_limit << 1
                self.upper_limit = (self.upper_limit << 1) + 1

                self.lower_limit &= _SAC.FULL_RANGE_BITMASK
                self.upper_limit &= _SAC.FULL_RANGE_BITMASK

    def flush(self) -> str:
        code = self.encoder.send(Settings.EOF_MARKER)

        self.num_pending_bits += 1
        bit = 0 if self.lower_limit < _SAC.QUARTER_RANGE else 1
        retval = code + f"{bit}{str(bit ^ 1) * (self.num_pending_bits + 1)}"

        self.reset()

        return retval

    def reset(self) -> None:
        self.__init__()


class AdaptiveDecoder:
    def __init__(self) -> None:
        self.lower_limit = 0
        self.upper_limit = _SAC.FULL_RANGE_BITMASK
        self.code_values = 0

        self.bitstream = BitIntegerBuffer()
        self._primed = False
        self._flushed = False

        self.codebook = AdaptiveArithmeticCodebook()
        self.decoder = self._decode()  # ! DO NOT ACTIVATE THE DECODER BEFORE INSTANTIATING CODE_VALUES

    def decode(self, bits: str | bytes | int) -> str:
        if not self._primed:
            if len(self.bitstream) < _SAC.PRECISION:
                self.bitstream.write(bits)
                return ""

            self.code_values = self.bitstream.read(_SAC.PRECISION)

            self._primed = True
            self.decoder.send(None)

        return self.decoder.send(bits)

    def _decode(self) -> Generator[str, int, None]:
        decoded_symbols = ""

        while True:
            if not self.bitstream and not self._flushed:
                bits = yield decoded_symbols
                if not self._flushed:
                    self.bitstream.write(bits)
                decoded_symbols = ""

            total_symbols = self.codebook.symbol_counts
            current_range = self.upper_limit - self.lower_limit + 1

            scaled_code_value = ((self.code_values - self.lower_limit + 1) * total_symbols - 1) // current_range

            sym, (sym_low, sym_high) = self.codebook.probability_symbol_search(scaled_code_value)

            if sym == Settings.EOF_MARKER:
                yield decoded_symbols

            decoded_symbols += sym
            self.upper_limit = self.lower_limit + (sym_high * current_range // total_symbols) - 1
            self.lower_limit = self.lower_limit + (sym_low * current_range // total_symbols)

            while True:

                # value's MSB is 0
                if self.upper_limit < _SAC.HALF_RANGE:
                    pass

                # value's MSB is 1
                elif self.lower_limit >= _SAC.HALF_RANGE:
                    self.lower_limit -= _SAC.HALF_RANGE
                    self.upper_limit -= _SAC.HALF_RANGE
                    self.code_values -= _SAC.HALF_RANGE

                # lower & upper limit are converging
                elif self.lower_limit >= _SAC.QUARTER_RANGE and self.upper_limit < _SAC.THREE_QUARTER_RANGE:
                    self.lower_limit -= _SAC.QUARTER_RANGE
                    self.upper_limit -= _SAC.QUARTER_RANGE
                    self.code_values -= _SAC.QUARTER_RANGE

                else:
                    # self.lower_limit < 25% AND self.upper_limit > 75%
                    # high & low must be at least 1/4 apart
                    break

                self.lower_limit = self.lower_limit << 1
                self.upper_limit = (self.upper_limit << 1) + 1

                if not self.bitstream and not self._flushed:
                    bits = yield decoded_symbols
                    if not self._flushed:
                        self.bitstream.write(bits)
                    decoded_symbols = ""

                self.code_values = (self.code_values << 1) + (self.bitstream.read(1) or 0)

    def flush(self) -> str:
        self._flushed = True
        retval = self.decoder.send(None)
        self.reset()
        return retval

    def reset(self) -> None:
        self.__init__()
