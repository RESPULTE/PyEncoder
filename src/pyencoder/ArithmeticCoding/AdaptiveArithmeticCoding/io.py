from typing import BinaryIO, TextIO

from pyencoder.utils.BitIO import BufferedBitOutput

from pyencoder.ArithmeticCoding.AdaptiveArithmeticCoding import AdaptiveDecoder, AdaptiveEncoder


def load(input_file: BinaryIO, output_file: TextIO = None) -> None | str:
    decoder = AdaptiveDecoder()
    if output_file:
        for symbol in decoder.decode(input_file):
            output_file.write(symbol)
        return None

    return "".join(decoder.decode(input_file))


def dump(input_file: TextIO | str, output_file: BinaryIO) -> None:
    bitstream = BufferedBitOutput(output_file)
    encoder = AdaptiveEncoder()

    while True:

        symbol = input_file.read(1)

        if not symbol:
            bitstream.write(encoder.flush())
            bitstream.flush()
            break

        bitstream.write(encoder.encode(symbol))
