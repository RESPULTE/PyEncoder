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

    for sym in codebook._all_symbols:
        codebook[sym] -= 1

    actual_catalogue = collections.Counter(StringData).most_common()
    assert set(codebook.symbol_catalogue).issuperset(set(actual_catalogue))


def test_adaptive_codebook_symbol_search(adaptive_codebook: AC.codebook.AdaptiveArithmeticCodebook) -> None:
    for sym in adaptive_codebook._all_symbols:
        adaptive_codebook[sym] -= 1

    for i in range(adaptive_codebook.total_symbols):
        sym = adaptive_codebook.get_symbol(i)
        sym_low, sym_high = adaptive_codebook.get_probability(sym)
        assert sym_low <= i < sym_high


def test_dump_and_load(StringData: str) -> None:
    txt_file = tempfile.TemporaryFile(mode="r+")
    with txt_file as input_file:
        input_file.write(StringData)
        input_file.flush()
        input_file.seek(0)

        with tempfile.TemporaryFile(mode="r+b") as output_file:
            AC.dump(input_file, output_file)
            output_file.seek(0)

            input_file = output_file
            with tempfile.TemporaryFile(mode="r+") as output_file:
                AC.load(input_file, output_file)
