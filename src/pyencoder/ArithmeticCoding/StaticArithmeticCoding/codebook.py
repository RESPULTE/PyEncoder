import bisect
import collections
from typing import List, Tuple

from pyencoder import Settings


class StaticArithmeticCodebook(collections.OrderedDict):
    """

    the codebook for Static version of Arithmetic Coding

    implemented using ordered dict to maintain the structure//indexing of the probability range

    """

    def __init__(self) -> None:
        self.symbol_probability_bounds: List[int] = []
        self.symbols: List[str] = []

        self.total_elems = 0

    @classmethod
    def from_dataset(cls, dataset: str) -> "StaticArithmeticCodebook":
        """
        generates codebook from dataset(uncounted)

        Args:
            dataset (str): strings

        Returns:
            StaticArithmeticCodebook: Codebook
        """
        counted_dataset = collections.OrderedDict(collections.Counter(dataset).most_common())
        return cls.from_counted_dataset(counted_dataset)

    @classmethod
    def from_counted_dataset(cls, counted_dataset: collections.OrderedDict[str, int]) -> "StaticArithmeticCodebook":
        """
        generate a codebook using counted dataset, in which the frequency of appearance for all the unique symbols in a string//dataset is counted

        Args:
            counted_dataset (collections.OrderedDict[str, int]):
            an ordered mapping of unqiue symbols with the frequency of appearance  of said symbols as the values

        Returns:
            StaticArithmeticCodebook: codebook
        """
        cummulative_proabability = 0
        codebook = cls()

        for sym, count in counted_dataset.items():
            sym_lower_limit = cummulative_proabability
            sym_upper_limit = cummulative_proabability + min(count, Settings.ArithmeticCoding.MAX_FREQUENCY)

            codebook[sym] = (sym_lower_limit, sym_upper_limit)
            codebook.symbol_probability_bounds.append(sym_lower_limit)

            cummulative_proabability = sym_upper_limit

        codebook.symbol_probability_bounds.append(sym_upper_limit)
        codebook.total_elems = cummulative_proabability
        codebook.symbols = list(codebook.keys())

        return codebook

    def search_symbol(self, probability: int) -> Tuple[str, Tuple[int, int]]:
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
        return (self.symbols[index], (sym_probs[index], sym_probs[index + 1]))
