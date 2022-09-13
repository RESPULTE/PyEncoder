import bisect
import itertools
from typing import OrderedDict, Tuple

from pyencoder import Settings


class AdaptiveArithmeticCodebook:
    """
    This is a codebook for the adaptive version of the Arithmetic Coding Algorithm

    it holds a catalogue of all valid symbols available and keeps track of
    each of their probability range, includng the cummulative probability range.

    The updating of symbols is really slow as its O(N) in time complexity, and is
    in fact the major performance bomb of this algorithm.

    [TODO]:
    1. Implement Fenwick Tree to speed up the updating process
    """

    def __init__(self):
        self.symbol_catalogue = OrderedDict({k: 1 for k in Settings.SYMBOLS})
        self.symbol_counts = sum(self.symbol_catalogue.values())
        self.symbol_probability_bounds = list(itertools.accumulate(self.symbol_catalogue.values(), initial=0))

    def probability_symbol_search(self, probability: int) -> Tuple[str, Tuple[int, int]]:
        """
        does a binary search with the given probability
        to get associated symbol, in which its range the proabability lies

        Args:
            probability (int): an integer that's scaled to the Codebook's range,
                               in other words, must lie within the uppermost/lowermost
                               bound of this codebook

        Returns:
            Tuple[str, Tuple[int, int]]: returns the symbol and the said symbol's probability range (upper/lower)
        """
        sym_probs = self.symbol_probability_bounds

        index = bisect.bisect_right(sym_probs, probability) - 1
        probability = (sym_probs[index], sym_probs[index + 1])
        symbol = Settings.SYMBOLS[index]

        self._update(symbol, index)

        return symbol, probability

    def catalogue_symbol(self, symbol: str) -> Tuple[int, int]:
        """
        catalogue the given symbol in the codebook and returns the
        said symbol's probability range (before updating)

        Args:
            symbol (str): the symbol

        Raises:
            ValueError: if an unknown symbol, that's not catalogued in the central "Settings" object is detected

        Returns:
            Tuple[int, int]: the probability range for said symbol (upper/lower)
        """
        sym_probs = self.symbol_probability_bounds

        try:
            index = Settings.SYMBOLS.index(symbol)
        except ValueError as err:
            raise ValueError("unknown symbol detected: {0}".format(symbol)) from err
        probability = (sym_probs[index], sym_probs[index + 1])

        self._update(symbol, index)

        return probability

    def _update(self, symbol: str, index: int) -> None:
        """
        an internal method, update the symbol's count and the symbol's probability range

        Args:
            symbol (str): the symbol
            index (int): the index of the symbol, mainly here for performance sake,
                         as we'd be getting the symbol's index even before entering this funciton
        """
        self.symbol_catalogue[symbol] += 1
        self.symbol_counts += 1

        for i in range(index + 1, Settings.NUM_SYMBOLS + 1):
            self.symbol_probability_bounds[i] += 1
