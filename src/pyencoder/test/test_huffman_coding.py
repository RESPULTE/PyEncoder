import tempfile
import pyencoder.HuffmanCoding.StaticHuffmanCoding.io as HC


def test_dump_and_load(StringData: str) -> None:
    with tempfile.TemporaryFile(mode="r+") as txt_file:
        txt_file.write("Never Gonna Give")
        txt_file.flush()
        txt_file.seek(0)

        with tempfile.TemporaryFile(mode="r+b") as encoded_file:
            HC.dump(txt_file, encoded_file)
            encoded_file.seek(0)

            with tempfile.TemporaryFile(mode="r+") as decoded_file:
                HC.load(encoded_file, decoded_file)

                assert decoded_file.read() == txt_file.read()
