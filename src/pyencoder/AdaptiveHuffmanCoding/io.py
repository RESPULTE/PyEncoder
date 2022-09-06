from typing import BinaryIO, TextIO
from .main import encode, decode
from pyencoder.utils.BitIO import BufferedBitInput, BufferedBitOutput
from pyencoder.config import main_config


def dump(input_file: TextIO, output_file: BinaryIO) -> None:
    bitstream = BufferedBitOutput(output_file)

    while True:

        symbol = input_file.read(1)

        if not symbol:
            bitstream.flush()
            break

        bitstream.write(encode(symbol))

    bitstream.write(encode(main_config.EOF_MARKER))


def load(input_file: BinaryIO, output_file: TextIO = None) -> str:
    bitstream = BufferedBitInput(input_file)
    decoder = decode(bitstream)

    if output_file:
        while True:
            try:
                symbol = next(decoder)
            except StopIteration:
                raise Exception("EOF not detected")

            if symbol == main_config.EOF_MARKER:
                break

            output_file.write(symbol)

        return

    decoded_data = ""
    while True:
        try:
            symbol = next(decoder)
        except StopIteration:
            raise Exception("EOF not detected")

        if symbol == main_config.EOF_MARKER:
            break
        decoded_data += symbol

    return
