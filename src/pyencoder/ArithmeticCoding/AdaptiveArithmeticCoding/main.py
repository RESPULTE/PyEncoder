from typing import Generator, Iterable

from pyencoder import Settings
from pyencoder.utils.BitIO import BufferedBitInput
from pyencoder.ArithmeticCoding.AdaptiveArithmeticCoding.codebook import AdaptiveArithmeticCodebook


class AdaptiveEncoder:
    def __init__(self):
        self.codebook = AdaptiveArithmeticCodebook()
        self.reset()

    def encode(self, symbol: str) -> str:
        return self.encoder.send(symbol)

    def _encode(self) -> Generator[str, str, None]:
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
                if self.upper_limit < Settings.ArithmeticCoding.HALF_RANGE:
                    code += "0" + "1" * self.num_pending_bits
                    self.num_pending_bits = 0

                elif self.lower_limit >= Settings.ArithmeticCoding.HALF_RANGE:
                    code += "1" + "0" * self.num_pending_bits
                    self.num_pending_bits = 0

                elif (
                    self.lower_limit >= Settings.ArithmeticCoding.QUARTER_RANGE
                    and self.upper_limit < Settings.ArithmeticCoding.THREE_QUARTER_RANGE
                ):
                    self.lower_limit -= Settings.ArithmeticCoding.QUARTER_RANGE
                    self.upper_limit -= Settings.ArithmeticCoding.QUARTER_RANGE
                    self.num_pending_bits += 1

                else:
                    break

                self.lower_limit = self.lower_limit << 1
                self.upper_limit = (self.upper_limit << 1) + 1

                self.lower_limit &= Settings.ArithmeticCoding.FULL_RANGE_BITMASK
                self.upper_limit &= Settings.ArithmeticCoding.FULL_RANGE_BITMASK

    def flush(self) -> str:
        code = self.encoder.send(Settings.EOF_MARKER)

        self.num_pending_bits += 1
        bit = 0 if self.lower_limit < Settings.ArithmeticCoding.QUARTER_RANGE else 1
        retval = code + f"{bit}{str(bit ^ 1) * (self.num_pending_bits + 1)}"

        self.reset()
        self.encoder.close()

        return retval

    def reset(self) -> None:
        self.lower_limit = 0
        self.upper_limit = Settings.ArithmeticCoding.FULL_RANGE_BITMASK
        self.num_pending_bits = 0

        self.codebook.reset()

        self.encoder = self._encode()
        self.encoder.send(None)


class AdaptiveDecoder:
    def __init__(self) -> None:
        self.codebook = AdaptiveArithmeticCodebook()
        self.reset()

    def decode(self, bindata: str) -> Iterable[str]:
        bitstream = BufferedBitInput(bindata, as_int=True)

        self.code_values = bitstream.read(Settings.ArithmeticCoding.PRECISION)

        while True:
            current_range = self.upper_limit - self.lower_limit + 1
            total_symbols = self.codebook.total_symbols

            scaled_code_value = ((self.code_values - self.lower_limit + 1) * total_symbols - 1) // current_range

            sym, (sym_low, sym_high) = self.codebook.probability_symbol_search(scaled_code_value)

            if sym == Settings.EOF_MARKER:
                self.reset()
                break

            yield sym
            self.upper_limit = self.lower_limit + (sym_high * current_range // total_symbols) - 1
            self.lower_limit = self.lower_limit + (sym_low * current_range // total_symbols)

            while True:

                # value's MSB is 0
                if self.upper_limit < Settings.ArithmeticCoding.HALF_RANGE:
                    pass

                # value's MSB is 1
                elif self.lower_limit >= Settings.ArithmeticCoding.HALF_RANGE:
                    self.lower_limit -= Settings.ArithmeticCoding.HALF_RANGE
                    self.upper_limit -= Settings.ArithmeticCoding.HALF_RANGE
                    self.code_values -= Settings.ArithmeticCoding.HALF_RANGE

                # lower & upper limit are converging
                elif (
                    self.lower_limit >= Settings.ArithmeticCoding.QUARTER_RANGE
                    and self.upper_limit < Settings.ArithmeticCoding.THREE_QUARTER_RANGE
                ):
                    self.lower_limit -= Settings.ArithmeticCoding.QUARTER_RANGE
                    self.upper_limit -= Settings.ArithmeticCoding.QUARTER_RANGE
                    self.code_values -= Settings.ArithmeticCoding.QUARTER_RANGE

                else:
                    # self.lower_limit < 25% AND self.upper_limit > 75%
                    # high & low must be at least 1/4 apart
                    break

                self.lower_limit = self.lower_limit << 1
                self.upper_limit = (self.upper_limit << 1) + 1
                self.code_values = (self.code_values << 1) + (bitstream.read(1) or 0)

    def reset(self) -> None:
        self.lower_limit = 0
        self.upper_limit = Settings.ArithmeticCoding.FULL_RANGE_BITMASK
        self.code_values = 0

        self.codebook.reset()
