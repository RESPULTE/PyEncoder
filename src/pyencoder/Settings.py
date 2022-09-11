import math
import string
import dataclasses
from typing import Any, Dict


class Singleton(type):
    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(Singleton, cls).__call__(*args, **kwargs)
        return cls._instances[cls]


@dataclasses.dataclass
class _Settings(metaclass=Singleton):
    ENDIAN: str = "big"

    SOF_MARKER: str = "\x0f"
    EOF_MARKER: str = "\xff"

    SYMBOLS: str = string.printable + SOF_MARKER + EOF_MARKER

    _NUM_SYMBOLS: int = dataclasses.field(init=False)
    _FIXED_CODE_SIZE: int = dataclasses.field(init=False)
    _FIXED_CODE_LOOKUP: Dict[str, str] = dataclasses.field(init=False)
    _FIXED_SYMBOL_LOOKUP: Dict[str, str] = dataclasses.field(init=False)

    def __post_init__(self) -> None:
        self.recalibrate()
        self.HuffmanCoding = self._HuffmanCoding()
        self.ArithmeticCoding = self._ArithmeticCoding()

    def recalibrate(self) -> None:
        self._NUM_SYMBOLS: int = len(self.SYMBOLS)
        self._FIXED_CODE_SIZE: int = math.ceil(math.log2(self._NUM_SYMBOLS))
        self._FIXED_CODE_LOOKUP: Dict[str, str] = {
            k: "{0:0{1}b}".format(i, self._FIXED_CODE_SIZE) for i, k in enumerate(self.SYMBOLS)
        }
        self._FIXED_SYMBOL_LOOKUP: Dict[str, str] = {v: k for k, v in self._FIXED_CODE_LOOKUP.items()}

    @property
    def NUM_SYMBOLS(self) -> int:
        return self._NUM_SYMBOLS

    @property
    def FIXED_CODE_SIZE(self) -> int:
        return self._FIXED_CODE_SIZE

    @property
    def FIXED_CODE_LOOKUP(self) -> Dict[str, str]:
        return self._FIXED_CODE_LOOKUP

    @property
    def FIXED_SYMBOL_LOOKUP(self) -> Dict[str, str]:
        return self._FIXED_SYMBOL_LOOKUP

    def __setattr__(self, __name: str, __value: Any) -> None:
        super().__setattr__(__name, __value)

        if __name == self.SYMBOLS:
            self.recalibrate()

    @dataclasses.dataclass
    class _HuffmanCoding:
        NUM_CODELENGTH: int = 16
        CODELENGTH_BITSIZE: int = 8

    @dataclasses.dataclass
    class _ArithmeticCoding:
        PRECISION: int = 32
        MAX_FREQUENCY: int = (1 << 16) - 1

        _FULL_RANGE: int = dataclasses.field(init=False)
        _HALF_RANGE: int = dataclasses.field(init=False)
        _QUARTER_RANGE: int = dataclasses.field(init=False)
        _THREE_QUARTER_RANGE: int = dataclasses.field(init=False)

        _FULL_RANGE_BITMASK: int = dataclasses.field(init=False)

        @property
        def FULL_RANGE(self) -> int:
            return self._FULL_RANGE

        @property
        def HALF_RANGE(self) -> int:
            return self._HALF_RANGE

        @property
        def QUARTER_RANGE(self) -> int:
            return self._QUARTER_RANGE

        @property
        def THREE_QUARTER_RANGE(self) -> int:
            return self._THREE_QUARTER_RANGE

        @property
        def FULL_RANGE_BITMASK(self) -> int:
            return self._FULL_RANGE_BITMASK

        def _recalibrate(self) -> None:
            self._FULL_RANGE = 1 << self.PRECISION
            self._HALF_RANGE = self._FULL_RANGE >> 1
            self._QUARTER_RANGE = self._HALF_RANGE >> 1
            self._THREE_QUARTER_RANGE = self._HALF_RANGE + self._QUARTER_RANGE
            self._FULL_RANGE_BITMASK = self._FULL_RANGE - 1

        def __setattr__(self, __name: str, __value: int) -> None:
            super().__setattr__(__name, __value)

            if __name == "PRECISION":
                self._recalibrate()
