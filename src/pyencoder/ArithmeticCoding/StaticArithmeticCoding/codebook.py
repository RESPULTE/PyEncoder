import bisect
import collections
from typing import List, Tuple


class ArithmeticCodebook(dict):
    def __init__(self) -> None:
        self.symbol_probability_bounds: List[int] = []
        self.total_elems = 0

    @classmethod
    def from_dataset(cls, dataset: str) -> "ArithmeticCodebook":
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

    def search_symbol(self, probability: int) -> Tuple[str, Tuple[int, int]]:
        sym_probs = self.symbol_probability_bounds
        index = bisect.bisect_right(sym_probs, probability) - 1
        return (self[index], (sym_probs[index], sym_probs[index + 1]))
