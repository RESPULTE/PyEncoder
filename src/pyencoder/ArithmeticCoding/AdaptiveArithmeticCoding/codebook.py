import bisect
import itertools
from typing import OrderedDict, Tuple

from pyencoder import Settings


class AdaptiveArithmeticCodebook:
    def __init__(self):
        self.symbol_catalogue = OrderedDict({k: 1 for k in Settings.SYMBOLS})
        self.symbol_counts = sum(self.symbol_catalogue.values())
        self.symbol_probability_bounds = list(itertools.accumulate(self.symbol_catalogue.values(), initial=0))

    def probability_symbol_search(self, probability: int) -> Tuple[str, Tuple[int, int]]:
        sym_probs = self.symbol_probability_bounds

        index = bisect.bisect_right(sym_probs, probability) - 1
        probability = (sym_probs[index], sym_probs[index + 1])
        symbol = Settings.SYMBOLS[index]

        self._update(symbol, index)

        return symbol, probability

    def catalogue_symbol(self, symbol: str) -> Tuple[int, int]:
        sym_probs = self.symbol_probability_bounds

        try:
            index = Settings.SYMBOLS.index(symbol)
        except ValueError as err:
            raise ValueError("unknown symbol detected: {0}".format(symbol)) from err
        probability = (sym_probs[index], sym_probs[index + 1])

        self._update(symbol, index)

        return probability

    def _update(self, symbol: str, index: int) -> None:
        self.symbol_catalogue[symbol] += 1
        self.symbol_counts += 1

        for i in range(index + 1, Settings.NUM_SYMBOLS + 1):
            self.symbol_probability_bounds[i] += 1
