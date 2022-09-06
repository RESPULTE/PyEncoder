from typing import BinaryIO, TextIO

from pyencoder.utils.BitIO import BufferedBitInput, BufferedBitOutput
from pyencoder.AdaptiveArithmeticCoding import decode, encode, flush
from pyencoder.config import ArithmeticCoding_config


def load(input_file: BinaryIO, output_file: TextIO = None) -> None | str:
    if output_file:
        for symbol in decode(input_file):
            output_file.write(symbol)
            print(symbol)
        return None

    return "".join(decode(input_file))


def dump(input_file: TextIO, output_file: BinaryIO) -> None:
    bitstream = BufferedBitOutput(output_file, ArithmeticCoding_config.PRECISION // 8)

    while True:

        symbol = input_file.read(1)

        if not symbol:
            bitstream.write(flush())
            bitstream.flush()
            break

        bitstream.write(encode(symbol))
