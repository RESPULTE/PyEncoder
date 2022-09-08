from typing import BinaryIO, TextIO

from pyencoder.utils.BitIO import BufferedBitOutput

from pyencoder.ArithmeticCoding.AdaptiveArithmeticCoding import decode, encode, flush
from pyencoder.ArithmeticCoding import Settings


def load(input_file: BinaryIO, output_file: TextIO = None) -> None | str:
    if output_file:
        for symbol in decode(input_file):
            output_file.write(symbol)
        return None

    return "".join(decode(input_file))


def dump(input_file: TextIO, output_file: BinaryIO) -> None:
    bitstream = BufferedBitOutput(output_file, Settings.PRECISION // 8)

    while True:

        symbol = input_file.read(1)

        if not symbol:
            bitstream.write(flush())
            bitstream.flush()
            break

        bitstream.write(encode(symbol))
