import tempfile
import pytest
import pyencoder.ArithmeticCoding.StaticArithmeticCoding as SAC


@pytest.mark.xfail
def test_dump_and_load(StringData: str) -> None:
    with tempfile.TemporaryFile(mode="r+") as txt_file:
        txt_file.write("Never Gonna Give")
        txt_file.flush()
        txt_file.seek(0)

        with tempfile.TemporaryFile(mode="r+b") as encoded_file:
            SAC.io.dump(txt_file, encoded_file)
            encoded_file.seek(0)

            with tempfile.TemporaryFile(mode="r+") as decoded_file:
                SAC.io.load(encoded_file, decoded_file)

                assert decoded_file.read() == txt_file.read()


def test_encode_decode(StringData: str) -> None:
    codebook, encoded_data = SAC.main.encode(StringData)
    decoded_data = SAC.main.decode(encoded_data, codebook)
    assert "".join(decoded_data) == StringData
