import string
import bisect
import itertools
import functools
import collections
from typing import List, OrderedDict, Tuple

from pyencoder.type_hints import ValidData, ValidDataset


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
        self._symbol_catalogue = OrderedDict({k: 1 for k in string.printable})
        self._symbol_counts = self._symbol_catalogue.values()
        self._all_symbols = self._symbol_catalogue.keys()

        self._symbol_catalogue_as_list = self._symbol_catalogue.items()

        self.calculate_symbol_probability_bounds = itertools.accumulate

    @property
    def total_symbols(self) -> int:
        return sum(self._symbol_counts)

    @property
    def symbol_probability_bounds(self) -> List[int]:
        return list(self.calculate_symbol_probability_bounds(tuple(self._symbol_counts)))

    @property
    def symbol_catalogue(self) -> List[Tuple[str, int]]:
        return list(self._symbol_catalogue_as_list)

    def get_symbol(self, probability: int) -> str:
        # using "less than"
        # if 'more than', the retval would be the lower bound of the next symbol // upper bound of said symbol (100% wrong), retval: next symbol's index
        # if "le", there's a chance that the retval would be the lower bound of the next symbol (maybe), retval: maybe next symbol's index, maybe the right symbol's index
        # if 'ge',  the retval would either be the lower bound of the next symbol (100% wrong), retval: next symbol's index
        index = bisect.bisect_left(self.symbol_probability_bounds, probability) - 1
        return self.symbol_catalogue[index][0]

    def get_probability(self, symbol: str) -> Tuple[int, int]:
        index = list(self._all_symbols).index(symbol)
        return self.symbol_probability_bounds[index], self.symbol_probability_bounds[index + 1]

    def __setitem__(self, symbol: str, count: int) -> None:
        if symbol not in self._symbol_catalogue:
            raise KeyError(f"The symbol {symbol} is not an ascii character.")

        self._symbol_catalogue[symbol] = count

    def __getitem__(self, symbol: str) -> str:
        return self._symbol_catalogue[symbol]
