from typing import BinaryIO, TextIO

from pyencoder.utils.BitIO import BufferedBitOutput
from pyencoder.HuffmanCoding.AdaptiveHuffmanCoding.main import AdaptiveDecoder, AdaptiveEncoder


def dump(input_file: TextIO, output_file: BinaryIO) -> None:
    encoder = AdaptiveEncoder()
    bitstream = BufferedBitOutput(output_file)

    while True:

        symbol = input_file.read(1)

        if not symbol:
            bitstream.write(encoder.flush())
            bitstream.flush()
            break

        bitstream.write(encoder.encode(symbol))


def load(input_file: BinaryIO, output_file: TextIO = None) -> str | None:
    decoder = AdaptiveDecoder()
    if output_file:
        for symbol in decoder.decode(input_file):
            output_file.write(symbol)
        return None

    return "".join(decoder.decode(input_file))
