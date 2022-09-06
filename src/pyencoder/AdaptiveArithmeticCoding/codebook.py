import bisect
import itertools
from typing import OrderedDict, Tuple

import pyencoder.config.main_config as main_config


class AdaptiveArithmeticCodebook:
    def __init__(self):
        self.symbol_catalogue = OrderedDict({k: 1 for k in main_config.SYMBOLS})
        self.symbol_counts = self.symbol_catalogue.values()
        self.symbol_probability_bounds = list(itertools.accumulate(self.symbol_counts, initial=0))

    @property
    def total_symbols(self) -> int:
        return sum(self.symbol_counts)

    def probability_symbol_search(self, probability: int) -> Tuple[str, Tuple[int, int]]:
        sym_probs = self.symbol_probability_bounds

        index = bisect.bisect_right(sym_probs, probability) - 1
        probability = (sym_probs[index], sym_probs[index + 1])
        symbol = main_config.SYMBOLS[index]

        self._update(symbol, index)

        return symbol, probability

    def catalogue_symbol(self, symbol: str) -> Tuple[int, int]:
        sym_probs = self.symbol_probability_bounds

        index = main_config.SYMBOLS.index(symbol)
        probability = (sym_probs[index], sym_probs[index + 1])

        self._update(symbol, index)

        return probability

    def _update(self, symbol: str, index: int) -> None:
        self.symbol_catalogue[symbol] += 1

        for i in range(index + 1, main_config.NUM_SYMBOLS + 1):
            self.symbol_probability_bounds[i] += 1
