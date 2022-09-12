import itertools
import pytest
import tempfile
import collections

from pyencoder.ArithmeticCoding.AdaptiveArithmeticCoding import codebook as AAC_codebook
from pyencoder.ArithmeticCoding.AdaptiveArithmeticCoding import io as AAC_io


@pytest.fixture
def adaptive_codebook(StringData) -> AAC_codebook.AdaptiveArithmeticCodebook:
    codebook = AAC_codebook.AdaptiveArithmeticCodebook()
    for sym, count in collections.Counter(StringData).most_common():
        codebook.symbol_catalogue[sym] = count
    codebook.symbol_probability_bounds = list(itertools.accumulate(codebook.symbol_catalogue.values(), initial=0))
    return codebook


def test_adaptive_codebook_symbol_search(adaptive_codebook: AAC_codebook.AdaptiveArithmeticCodebook) -> None:
    for i in range(1, adaptive_codebook.symbol_counts, 2):
        _, (sym_low, sym_high) = adaptive_codebook.probability_symbol_search(i)
        assert sym_low <= i <= sym_high


def test_adaptive_codebook_catalogue():
    ...
