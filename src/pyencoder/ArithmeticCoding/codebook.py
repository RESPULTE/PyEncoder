import string
import bisect
import itertools
import functools
import collections
from typing import List, OrderedDict, Tuple

from pyencoder.type_hints import ValidData, ValidDataset
import pyencoder.config as main_config

SYMBOLS = string.printable + main_config.EOF_MARKER


class ArithmeticCodebook(dict):
    def __init__(self) -> None:
        self.symbol_probability_bounds = []
        self.total_elems = 0

    @classmethod
    def from_dataset(cls, dataset: ValidDataset) -> "ArithmeticCodebook":
        cummulative_proabability = 0
        codebook = cls()

        for sym, count in collections.Counter(dataset).most_common():
            sym_lower_limit = cummulative_proabability
            sym_upper_limit = cummulative_proabability + count

            codebook[sym] = (sym_lower_limit, sym_upper_limit)
            codebook.symbol_probability_bounds.append(sym_lower_limit)

            cummulative_proabability = sym_upper_limit

        codebook.symbol_probability_bounds.append(sym_upper_limit)
        codebook.total_elems = cummulative_proabability

        return codebook

    def search_symbol(self, probability: int) -> Tuple[ValidData, Tuple[int, int]]:
        index = bisect.bisect_right(self.symbol_probability_bounds, probability) - 1
        return (self[index], (self.symbol_probability_bounds[index], self.symbol_probability_bounds[index + 1]))


# * IMPLEMENT 'lru_cache' FOR 'calculate_symbol_probability_bounds'
class AdaptiveArithmeticCodebook:
    def __init__(self):
        self._symbol_catalogue = OrderedDict({k: 1 for k in SYMBOLS})
        self._symbol_counts = self._symbol_catalogue.values()

        self.calculate_symbol_probability_bounds = itertools.accumulate

    @property
    def total_symbols(self) -> int:
        return sum(self._symbol_counts)

    @property
    def symbol_catalogue(self) -> List[Tuple[str, int]]:
        return list(self._symbol_catalogue.items())

    @property
    def symbol_probability_bounds(self) -> List[int]:
        return list(self.calculate_symbol_probability_bounds((0, *self._symbol_counts)))

    def get_symbol(self, probability: int) -> str:
        index = bisect.bisect_right(self.symbol_probability_bounds, probability) - 1
        return SYMBOLS[index]

    def get_probability(self, symbol: str) -> Tuple[int, int]:
        index = SYMBOLS.index(symbol)
        return tuple(self.symbol_probability_bounds[index : index + 2])

    def __setitem__(self, symbol: str, count: int) -> None:
        if symbol not in self._symbol_catalogue:
            raise KeyError(f"The symbol {symbol} is not an ascii character.")

        self._symbol_catalogue[symbol] = count

    def __getitem__(self, symbol: str) -> str:
        return self._symbol_catalogue[symbol]
