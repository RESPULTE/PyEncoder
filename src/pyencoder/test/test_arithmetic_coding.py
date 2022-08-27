import tempfile
import pytest
import tempfile
import collections
from pyencoder import ArithmeticCoding as AC


@pytest.fixture
def adaptive_codebook(StringData) -> AC.codebook.AdaptiveArithmeticCodebook:
    codebook = AC.codebook.AdaptiveArithmeticCodebook()
    for sym, count in collections.Counter(StringData).most_common():
        codebook[sym] = count
    return codebook


def test_adaptive_codebook_symbol_count_increment(StringData: str) -> None:
    codebook = AC.codebook.AdaptiveArithmeticCodebook()
    for sym in StringData:
        codebook[sym] += 1

    for sym, _ in codebook.symbol_catalogue:
        codebook[sym] -= 1

    actual_catalogue = collections.Counter(StringData).most_common()
    assert set(codebook.symbol_catalogue).issuperset(set(actual_catalogue))


def test_adaptive_codebook_symbol_search(adaptive_codebook: AC.codebook.AdaptiveArithmeticCodebook) -> None:
    for i in range(1, adaptive_codebook.total_symbols, 2):
        sym = adaptive_codebook.get_symbol(i)
        sym_low, sym_high = adaptive_codebook.get_probability(sym)
        assert sym_low <= i <= sym_high


def test_dump_and_load(StringData: str) -> None:
    with tempfile.TemporaryFile(mode="r+") as txt_file:
        txt_file.write(StringData)
        txt_file.flush()
        txt_file.seek(0)

        with tempfile.TemporaryFile(mode="r+b") as encoded_file:
            AC.dump(txt_file, encoded_file)
            encoded_file.seek(0)

            with tempfile.TemporaryFile(mode="r+") as decoded_file:
                AC.load(encoded_file, decoded_file)

                assert decoded_file.read() == txt_file.read()
