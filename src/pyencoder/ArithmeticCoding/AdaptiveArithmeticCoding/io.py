from typing import BinaryIO, TextIO

from pyencoder.ArithmeticCoding.AdaptiveArithmeticCoding import AdaptiveDecoder, AdaptiveEncoder
from pyencoder.utils.BitIO.output import BufferedStringOutput
from pyencoder.utils.BitIO.input import BufferedStringInput


def dump(input_file: TextIO | str, output_file: BinaryIO) -> None:
    """
    reads text from a file or string, encode 'em and dump them into an output file

    Args:
        input_file (TextIO | str): a file containing text or just some strings
        output_file (BinaryIO): a file that can be written with bytes
    """
    encoder = AdaptiveEncoder()
    bit_output = BufferedStringOutput(output_file)

    for symbol in input_file.read():
        bit_output.write(encoder.encode(symbol))

    bit_output.write(encoder.flush())
    bit_output.flush()


def load(input_file: BinaryIO, output_file: TextIO = None) -> None | str:
    """
    reads encoded data from a file, decode 'em and loads them into a file (if any)

    Args:
        input_file (BinaryIO): a file with encoded data
        output_file (TextIO, optional): an output file, will return strings if not given. Defaults to None.

    Raises:
        EOFError: if the input file doesnt contain anything

    Returns:
        None | str: if output file is not provided, strings will be returned instead
    """
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
                raise EOFError("EOF without any data")
            return decoded_data
        decoded_data += decoder.decode(encoded_bits)
