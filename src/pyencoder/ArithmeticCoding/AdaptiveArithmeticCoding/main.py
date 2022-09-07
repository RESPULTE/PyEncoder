from typing import Generator, Iterable

from pyencoder.utils.BitIO import BufferedBitInput
from pyencoder import Config

from pyencoder.ArithmeticCoding.AdaptiveArithmeticCoding.codebook import AdaptiveArithmeticCodebook
from pyencoder.ArithmeticCoding import Settings


class AdaptiveArithmeticEncoder:
    def __init__(self):
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
                if self.upper_limit < Settings.HALF_RANGE:
                    code += "0" + "1" * self.num_pending_bits
                    self.num_pending_bits = 0

                elif self.lower_limit >= Settings.HALF_RANGE:
                    code += "1" + "0" * self.num_pending_bits
                    self.num_pending_bits = 0

                elif self.lower_limit >= Settings.QUARTER_RANGE and self.upper_limit < Settings.THREE_QUARTER_RANGE:
                    self.lower_limit -= Settings.QUARTER_RANGE
                    self.upper_limit -= Settings.QUARTER_RANGE
                    self.num_pending_bits += 1

                else:
                    break

                self.lower_limit = self.lower_limit << 1
                self.upper_limit = (self.upper_limit << 1) + 1

                self.lower_limit &= Settings.FULL_RANGE_BITMASK
                self.upper_limit &= Settings.FULL_RANGE_BITMASK

    def flush(self) -> str:
        code = self.encoder.send(Config["EOF_MARKER"])

        self.num_pending_bits += 1
        bit = 0 if self.lower_limit < Settings.QUARTER_RANGE else 1
        retval = code + f"{bit}{str(bit ^ 1) * (self.num_pending_bits + 1)}"

        self.reset()
        return retval

    def reset(self) -> None:
        self.lower_limit = 0
        self.upper_limit = Settings.FULL_RANGE_BITMASK
        self.num_pending_bits = 0

        self.codebook = AdaptiveArithmeticCodebook()

        self.encoder = self._encode()
        self.encoder.send(None)


encoder = AdaptiveArithmeticEncoder()
encode = encoder.encode
flush = encoder.flush


class AdaptiveArithmeticDecoder:
    def __init__(self) -> None:
        self.reset()

    def decode(self, bindata: str) -> Iterable[str]:
        bitstream = BufferedBitInput(bindata, Settings.PRECISION // 8, as_int=True)

        for _ in range(Settings.PRECISION):
            self.code_values = (self.code_values << 1) + bitstream.read(1)

        while True:
            current_range = self.upper_limit - self.lower_limit + 1
            total_symbols = self.codebook.total_symbols

            scaled_code_value = ((self.code_values - self.lower_limit + 1) * total_symbols - 1) // current_range

            sym, (sym_low, sym_high) = self.codebook.probability_symbol_search(scaled_code_value)

            if sym == Config["EOF_MARKER"]:
                self.reset()
                break

            yield sym
            self.upper_limit = self.lower_limit + (sym_high * current_range // total_symbols) - 1
            self.lower_limit = self.lower_limit + (sym_low * current_range // total_symbols)

            while True:

                # value's MSB is 0
                if self.upper_limit < Settings.HALF_RANGE:
                    pass

                # value's MSB is 1
                elif self.lower_limit >= Settings.HALF_RANGE:
                    self.lower_limit -= Settings.HALF_RANGE
                    self.upper_limit -= Settings.HALF_RANGE
                    self.code_values -= Settings.HALF_RANGE

                # lower & upper limit are converging
                elif self.lower_limit >= Settings.QUARTER_RANGE and self.upper_limit < Settings.THREE_QUARTER_RANGE:
                    self.lower_limit -= Settings.QUARTER_RANGE
                    self.upper_limit -= Settings.QUARTER_RANGE
                    self.code_values -= Settings.QUARTER_RANGE

                else:
                    # self.lower_limit < 25% AND self.upper_limit > 75%
                    # high & low must be at least 1/4 apart
                    break

                self.lower_limit = self.lower_limit << 1
                self.upper_limit = (self.upper_limit << 1) + 1
                self.code_values = (self.code_values << 1) + (bitstream.read(1) or 0)

    def reset(self) -> None:
        self.lower_limit = 0
        self.upper_limit = Settings.FULL_RANGE_BITMASK
        self.code_values = 0

        self.codebook = AdaptiveArithmeticCodebook()


decode = AdaptiveArithmeticDecoder().decode
