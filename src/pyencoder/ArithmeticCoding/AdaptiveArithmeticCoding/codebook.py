import bisect
import itertools
from typing import OrderedDict, Tuple

from pyencoder import Settings


def getsum(BITTree, i):
    s = 0  # initialize result

    # index in BITree[] is 1 more than the index in arr[]
    i = i + 1

    # Traverse ancestors of BITree[index]
    while i > 0:

        # Add current element of BITree to sum
        s += BITTree[i]

        # Move index to parent node in getSum View
        i -= i & (-i)
    return s


# Updates a node in Binary Index Tree (BITree) at given index
# in BITree. The given value 'val' is added to BITree[i] and
# all of its ancestors in tree.
def updatebit(BITTree, n, i, v):

    # index in BITree[] is 1 more than the index in arr[]
    i += 1

    # Traverse all ancestors and add 'val'
    while i <= n:

        # Add 'val' to current node of BI Tree
        BITTree[i] += v

        # Update index to that of parent in update View
        i += i & (-i)


# Constructs and returns a Binary Indexed Tree for given
# array of size n.
def construct(arr, n):

    # Create and initialize BITree[] as 0
    BITTree = [0] * (n + 1)

    # Store the actual values in BITree[] using update()
    for i in range(n):
        updatebit(BITTree, n, i, arr[i])

    # Uncomment below lines to see contents of BITree[]
    # for i in range(1,n+1):
    #     print BITTree[i],
    return BITTree


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
