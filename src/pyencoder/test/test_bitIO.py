from pyencoder.utils.BitIO import BufferedBitInput, BufferedBitOutput
import tempfile
import pytest


def test_str_read_iter(StringData: str) -> None:
    with tempfile.TemporaryFile() as tmp:
        tmp.write(StringData.encode("utf-8"))
        tmp.seek(0)

        reader = BufferedBitInput(tmp)

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


def test_int_read_iter(StringData: str) -> None:
    with tempfile.TemporaryFile() as tmp:
        tmp.write(StringData.encode("utf-8"))
        tmp.seek(0)

        reader = BufferedBitInput(tmp, as_int=True)

        buffer = 0
        buffer_size = 0
        output = []
        for i in reader:
            buffer = (buffer << 1) | i
            buffer_size += 1

            if buffer_size == 8:
                output.append(chr(buffer))
                buffer_size = 0
                buffer = 0

    assert "".join(output) == StringData


def test_str_read(StringData: str) -> None:
    with tempfile.TemporaryFile() as tmp:
        tmp.write(StringData.encode("ascii"))
        tmp.seek(0)

        reader = BufferedBitInput(tmp)

        buffer_size = 0
        buffer = ""
        output = []
        while True:
            new_bit = reader.read()
            if not new_bit:
                break

            buffer += new_bit
            buffer_size += 1

            if buffer_size >= 8:
                buffer, symbol_bits = buffer[8:], buffer[:8]
                output.append(chr(int(symbol_bits, 2)))
                buffer_size -= 8

    assert "".join(output) == StringData


def test_int_read(StringData: str) -> None:
    with tempfile.TemporaryFile() as tmp:
        tmp.write(StringData.encode("ascii"))
        tmp.seek(0)

        reader = BufferedBitInput(tmp, as_int=True)

        buffer_size = 0
        buffer = 0
        output = []
        while True:
            new_bit = reader.read()
            if new_bit == None:
                break

            buffer = (buffer << 1) | new_bit
            buffer_size += 1

            if buffer_size >= 8:
                i = buffer_size - 8
                symbol_bits = (buffer & (((1 << 8) - 1) << i)) >> i
                buffer = buffer & ((1 << i) - 1)
                output.append(chr(symbol_bits))
                buffer_size -= 8

    assert "".join(output) == StringData


def test_bit_write(StringData) -> None:
    with tempfile.TemporaryFile() as tmp:
        writer = BufferedBitOutput(tmp)
        for s in StringData:
            writer.write(bin(ord(s))[2:].zfill(8))
        writer.flush()

        tmp.seek(0)

        assert tmp.read().decode("utf-8") == StringData
