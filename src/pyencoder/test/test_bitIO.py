from pyencoder.utils.BitIO import BufferedStringInput, BufferedIntegerInput, BufferedIntegerOutput, BufferedStringOutput
import tempfile
import pytest


def test_str_read_iter(StringData: str) -> None:
    with tempfile.TemporaryFile() as tmp:
        tmp.write(StringData.encode("utf-8"))
        tmp.seek(0)

        reader = BufferedStringInput(tmp)

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

        reader = BufferedIntegerInput(tmp)

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


@pytest.mark.parametrize("n", [1, 3, 7, 10, 20, 64, 100])
def test_str_read(StringData: str, n: int) -> None:
    with tempfile.TemporaryFile() as tmp:
        tmp.write(StringData.encode("ascii"))
        tmp.seek(0)

        reader = BufferedStringInput(tmp)

        buffer_size = 0
        buffer = ""
        output = []
        while True:
            new_bits = reader.read(n)
            if not new_bits:
                break

            buffer += new_bits
            buffer_size += len(new_bits)

            while buffer_size >= 8:
                buffer, symbol_bits = buffer[8:], buffer[:8]
                output.append(chr(int(symbol_bits, 2)))
                buffer_size -= 8

    assert "".join(output) == StringData


@pytest.mark.parametrize("n", [1, 8])
def test_int_read(StringData: str, n: int) -> None:
    with tempfile.TemporaryFile() as tmp:
        tmp.write(StringData.encode("ascii"))
        tmp.seek(0)

        reader = BufferedIntegerInput(tmp)

        buffer_size = 0
        buffer = 0
        output = []
        while True:
            new_bits = reader.read(n)
            if new_bits == None:
                break

            buffer = (buffer << n) | new_bits
            buffer_size += n

            while buffer_size >= 8:
                i = buffer_size - 8
                symbol_bits = (buffer & (((1 << 8) - 1) << i)) >> i
                buffer = buffer & ((1 << i) - 1)
                new_symbol = chr(symbol_bits)
                output.append(new_symbol)
                buffer_size -= 8

    assert "".join(output) == StringData


def test_bit_write(StringData) -> None:
    with tempfile.TemporaryFile() as tmp:
        writer = BufferedStringOutput(tmp)
        for s in StringData:
            writer.write(bin(ord(s))[2:].zfill(8))
        writer.flush()

        tmp.seek(0)

        assert tmp.read().decode("utf-8") == StringData


def test_bit_bulk_write(StringData) -> None:
    with tempfile.TemporaryFile() as tmp:
        bindata = ""
        for s in StringData:
            bindata += bin(ord(s))[2:].zfill(8)

        writer = BufferedStringOutput(tmp)
        writer.write(bindata)
        writer.flush()

        tmp.seek(0)

        assert tmp.read().decode("utf-8") == StringData
