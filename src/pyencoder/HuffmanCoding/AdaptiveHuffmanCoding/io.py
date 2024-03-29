from typing import BinaryIO, TextIO

from pyencoder.HuffmanCoding.AdaptiveHuffmanCoding.main import AdaptiveDecoder, AdaptiveEncoder
from pyencoder.utils.BitIO.output import BufferedStringOutput
from pyencoder.utils.BitIO.input import BufferedStringInput


def dump(input_file: TextIO | str, output_file: BinaryIO) -> None:
    bit_output = BufferedStringOutput(output_file)
    encoder = AdaptiveEncoder()

    for symbol in input_file.read():
        bit_output.write(encoder.encode(symbol))

    if "symbol" not in locals():
        raise EOFError("EOF reached without any data")

    bit_output.write(encoder.flush())
    bit_output.flush()


def load(input_file: BinaryIO, output_file: TextIO = None) -> str | None:
    decoder = AdaptiveDecoder()
    bit_input = BufferedStringInput(input_file)

    if output_file:
        while True:
            encoded_bits = bit_input.read(32)
            if not encoded_bits:
                output_file.write(decoder.flush())
                return
            output_file.write(decoder.decode(encoded_bits))

    decoded_data = ""

    while True:
        encoded_bits = bit_input.read(32)
        if not encoded_bits:
            decoded_data += decoder.flush()
            if not decoded_data:
                raise EOFError("EOF reached without any data")

            return decoded_data
        decoded_data += decoder.decode(encoded_bits)
