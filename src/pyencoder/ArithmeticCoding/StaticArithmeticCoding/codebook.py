import bisect
import collections
from typing import List, Tuple

from pyencoder.ArithmeticCoding import Settings


class ArithmeticCodebook(collections.OrderedDict):
    def __init__(self) -> None:
        self.symbol_probability_bounds: List[int] = []
        self.symbols: List[str] = []

        self.total_elems = 0

    @classmethod
    def from_dataset(cls, dataset: str) -> "ArithmeticCodebook":
        counted_symbols = collections.Counter(dataset).most_common()
        cummulative_proabability = 0
        codebook = cls()

        for sym, count in counted_symbols:
            sym_lower_limit = cummulative_proabability
            sym_upper_limit = cummulative_proabability + min(count, Settings.MAX_FREQUENCY)

            codebook[sym] = (sym_lower_limit, sym_upper_limit)
            codebook.symbol_probability_bounds.append(sym_lower_limit)

            cummulative_proabability = sym_upper_limit

        codebook.symbol_probability_bounds.append(sym_upper_limit)
        codebook.total_elems = cummulative_proabability
        codebook.symbols = list(codebook.keys())

        return codebook

    def search_symbol(self, probability: int) -> Tuple[str, Tuple[int, int]]:
        sym_probs = self.symbol_probability_bounds
        index = bisect.bisect_right(sym_probs, probability) - 1
        return (self.symbols[index], (sym_probs[index], sym_probs[index + 1]))
