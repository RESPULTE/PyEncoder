import tempfile
import pytest
from pyencoder.ArithmeticCoding import StaticArithmeticCoding, AdaptiveArithmeticCoding
from pyencoder.HuffmanCoding import StaticHuffmanCoding, AdaptiveHuffmanCoding


@pytest.mark.parametrize(
    "algorithm", [StaticArithmeticCoding, AdaptiveArithmeticCoding, StaticHuffmanCoding, AdaptiveHuffmanCoding]
)
def test_dump_and_load(StringData: str, algorithm: object) -> None:
    encoder = algorithm.io.dump
    decoder = algorithm.io.load

    with tempfile.TemporaryFile(mode="r+") as txt_file:
        txt_file.write(StringData)
        txt_file.flush()
        txt_file.seek(0)

        with tempfile.TemporaryFile(mode="r+b") as encoded_file, tempfile.TemporaryFile(mode="r+") as decoded_file:
            encoder(txt_file, encoded_file)
            encoded_file.seek(0)

            decoder(encoded_file, decoded_file)

            assert decoded_file.read() == txt_file.read()


@pytest.mark.parametrize("algorithm", [StaticArithmeticCoding, StaticHuffmanCoding])
def test_static_encode_decode(StringData: str, algorithm: object) -> None:
    encoder = algorithm.main.encode
    decoder = algorithm.main.decode

    codebook, encoded_data = encoder(StringData)
    decoded_data = decoder(codebook, encoded_data)
    assert "".join(decoded_data) == StringData


@pytest.mark.parametrize("algorithm", [AdaptiveArithmeticCoding, AdaptiveHuffmanCoding])
def test_adaptive_encode_decode(StringData: str, algorithm: object) -> None:
    encoder = algorithm.main.AdaptiveEncoder()
    decoder = algorithm.main.AdaptiveDecoder()

    encoded_data = ""
    for sym in StringData:
        encoded_data += encoder.encode(sym)
    encoded_data += encoder.flush()

    decoded_data = ""
    for sym in decoder.decode(encoded_data):
        decoded_data += sym

    assert decoded_data == StringData
