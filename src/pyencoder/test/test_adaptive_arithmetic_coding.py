import itertools
import tempfile
import pytest
import tempfile
import collections

from pyencoder.AdaptiveArithmeticCoding import codebook as AAC_codebook
from pyencoder.AdaptiveArithmeticCoding import io as AAC_io


@pytest.fixture
def adaptive_codebook(StringData) -> AAC_codebook.AdaptiveArithmeticCodebook:
    codebook = AAC_codebook.AdaptiveArithmeticCodebook()
    for sym, count in collections.Counter(StringData).most_common():
        codebook.symbol_catalogue[sym] = count
    codebook.symbol_probability_bounds = list(itertools.accumulate(codebook.symbol_counts, initial=0))
    return codebook


def test_adaptive_codebook_symbol_search(adaptive_codebook: AAC_codebook.AdaptiveArithmeticCodebook) -> None:
    for i in range(1, adaptive_codebook.total_symbols, 2):
        _, (sym_low, sym_high) = adaptive_codebook.probability_symbol_search(i)
        assert sym_low <= i <= sym_high


def test_dump_and_load(StringData: str) -> None:
    with tempfile.TemporaryFile(mode="r+") as txt_file:
        txt_file.write(StringData)
        txt_file.flush()
        txt_file.seek(0)

        with tempfile.TemporaryFile(mode="r+b") as encoded_file:
            AAC_io.dump(txt_file, encoded_file)
            encoded_file.seek(0)

            with tempfile.TemporaryFile(mode="r+") as decoded_file:
                AAC_io.load(encoded_file, decoded_file)

                assert decoded_file.read() == txt_file.read()
