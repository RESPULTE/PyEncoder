from typing import BinaryIO, TextIO

from .main import encode, flush, decode

from pyencoder.utils.BitIO import BufferedBitOutput


def dump(input_file: TextIO, output_file: BinaryIO) -> None:
    bitstream = BufferedBitOutput(output_file)

    while True:

        symbol = input_file.read(1)

        if not symbol:
            bitstream.write(flush())
            bitstream.flush()
            break

        bitstream.write(encode(symbol))


def load(input_file: BinaryIO, output_file: TextIO = None) -> str | None:
    if output_file:
        for symbol in decode(input_file):
            output_file.write(symbol)
        return None

    return "".join(decode(input_file))
