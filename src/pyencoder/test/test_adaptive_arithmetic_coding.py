import itertools
import pytest
import tempfile
import collections

from pyencoder.ArithmeticCoding.AdaptiveArithmeticCoding import AdaptiveEncoder, AdaptiveDecoder
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


def test_EOF_on_input():
    None_existant_data = ""
    encoder = AAC_io.dump
    decoder = AAC_io.load

    with tempfile.TemporaryFile(mode="r+") as txt_file:
        txt_file.write(None_existant_data)
        txt_file.flush()
        txt_file.seek(0)

        with tempfile.TemporaryFile(mode="r+b") as encoded_file, tempfile.TemporaryFile(mode="r+") as decoded_file:
            encoder(txt_file, encoded_file)
            encoded_file.seek(0)

            decoder(encoded_file, decoded_file)

            assert decoded_file.read() == txt_file.read()


def test_flush_before_primed(StringData: str):
    encoder = AdaptiveEncoder()
    decoder = AdaptiveDecoder()

    encoded_data = ""
    for sym in StringData:
        encoded_data += encoder.encode(sym)
    encoded_data += encoder.flush()

    decoded_data = ""
    for i in range(0, len(encoded_data), 8):
        decoded_data += decoder.decode(encoded_data[i : i + 8])
        if i > 250:
            break

    decoded_data += decoder.flush()
    assert any(seg in StringData for seg in decoded_data.split(" "))
