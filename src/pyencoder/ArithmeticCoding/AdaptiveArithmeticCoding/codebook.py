import bisect
import itertools
from typing import OrderedDict, Tuple

from pyencoder import Settings


class AdaptiveArithmeticCodebook:
    def __init__(self):
        self.symbol_catalogue = OrderedDict({k: 1 for k in Settings.SYMBOLS})
        self.symbol_counts = self.symbol_catalogue.values()
        self.symbol_probability_bounds = list(itertools.accumulate(self.symbol_counts, initial=0))

    @property
    def total_symbols(self) -> int:
        return sum(self.symbol_counts)

    def probability_symbol_search(self, probability: int) -> Tuple[str, Tuple[int, int]]:
        sym_probs = self.symbol_probability_bounds

        index = bisect.bisect_right(sym_probs, probability) - 1
        probability = (sym_probs[index], sym_probs[index + 1])
        symbol = Settings.SYMBOLS[index]

        self._update(symbol, index)

        return symbol, probability

    def catalogue_symbol(self, symbol: str) -> Tuple[int, int]:
        sym_probs = self.symbol_probability_bounds

        index = Settings.SYMBOLS.index(symbol)
        probability = (sym_probs[index], sym_probs[index + 1])

        self._update(symbol, index)

        return probability

    def _update(self, symbol: str, index: int) -> None:
        self.symbol_catalogue[symbol] += 1

        for i in range(index + 1, Settings.NUM_SYMBOLS + 1):
            if self.symbol_probability_bounds[i] < Settings.ArithmeticCoding.MAX_FREQUENCY:
                self.symbol_probability_bounds[i] += 1
