from pyencoder import bitIO
import tempfile
import pytest


def test_bit_read_iter(StringData: str) -> None:
    with tempfile.TemporaryFile() as tmp:
        tmp.write(StringData.encode("utf-8"))
        tmp.seek(0)

        reader = bitIO.BufferedBitOutput(tmp)

        buffer = 0
        buffer_size = 0
        output = []
        for i in reader:
            buffer = (buffer << 1) | int(i)
            buffer_size += 1

            if buffer_size == 8:
                output.append(chr(buffer))
                buffer_size = 0
                buffer = 0

    assert "".join(output) == StringData


@pytest.mark.parametrize("numbit", [1, 2, 3, 5, 7, 9])
def test_bit_read(StringData: str, numbit: int) -> None:
    with tempfile.TemporaryFile() as tmp:
        tmp.write(StringData.encode("ascii"))
        tmp.seek(0)

        reader = bitIO.BufferedBitOutput(tmp)

        buffer_size = 0
        buffer = ""
        output = []
        while True:
            new_bit = reader.read(numbit)
            if not new_bit:
                break
            buffer += new_bit
            buffer_size += numbit

            if buffer_size >= 8:
                buffer, symbol_bits = buffer[8:], buffer[:8]
                output.append(chr(int(symbol_bits, 2)))
                buffer_size -= 8

    assert "".join(output) == StringData


def test_bit_write(StringData) -> None:
    with tempfile.TemporaryFile() as tmp:
        writer = bitIO.BufferedBitInput(tmp)
        for s in StringData:
            writer.write(bin(ord(s))[2:].zfill(8))
        writer.flush()

        tmp.seek(0)

        assert tmp.read().decode("utf-8") == StringData
