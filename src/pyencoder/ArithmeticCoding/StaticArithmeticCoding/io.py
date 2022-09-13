from collections import OrderedDict
from typing import BinaryIO, TextIO

from pyencoder import Settings
from pyencoder.utils.BitIO.input import BufferedStringInput

from pyencoder.ArithmeticCoding.StaticArithmeticCoding.main import decode, encode
from pyencoder.ArithmeticCoding.StaticArithmeticCoding.codebook import StaticArithmeticCodebook
from pyencoder.utils.BitIO.output import BufferedStringOutput


def load(input_source: BinaryIO, output_file: TextIO | None) -> None | str:
    """
    reads encoded data from a file, decode 'em and loads them into a file (if any)

    Args:
        input_file (BinaryIO): a file with encoded data
        output_file (TextIO, optional): an output file, will return strings if not given. Defaults to None.

    Returns:
        None | str: if output file is not provided, strings will be returned instead
    """
    codebook, leftover_bits = generate_codebook_from_header(input_source)

    encoded_data = "".join(f"{x:08b}" for x in input_source.read())

    encoded_data = encoded_data.rjust(8 * -(-len(encoded_data) // 8), "0")
    decoded_data = decode(codebook, leftover_bits + encoded_data)
    if not output_file:
        return decoded_data

    output_file.write("".join(decoded_data))


def dump(input_source: TextIO | str, output_file: BinaryIO) -> None:
    """
    reads text from a file or string, encode 'em and dump them into an output file

    Args:
        input_file (TextIO | str): a file containing text or just some strings
        output_file (BinaryIO): a file that can be written with bytes

    Raises:
        TypeError: if the input_source is not a file containing text or string
    """

    if hasattr(input_source, "read"):
        input_source = input_source.read()

    elif not isinstance(input_source, str):
        raise TypeError(f"Invalid type: {type(input_source).__name__}")

    codebook, encoded_data = encode(input_source)
    header = generate_header_from_codebook(codebook)

    if not output_file:
        return header + encoded_data

    data = header + encoded_data

    size = len(data)
    data = data.ljust(8 * -(-size // 8), "0")

    bytes_to_output = bytes([int(data[i : i + 8], 2) for i in range(0, len(data), 8)])
    output_file.write(bytes_to_output)


def generate_header_from_codebook(codebook: StaticArithmeticCodebook) -> str:
    """
    generate a header from a codebook containning the neccessary info the decode the data

    Args:
        codebook (StaticArithmeticCodebook): a codebook, duh

    Returns:
        str: bitcodes, string made of only 1s and 0s
    """
    header = ""

    for sym, (sym_low, sym_high) in codebook.items():
        sym_code = Settings.FIXED_CODE_LOOKUP[sym]
        count_code = "{0:0{num}b}".format(sym_high - sym_low, num=Settings.ArithmeticCoding.MAX_FREQUENCY_BITSIZE)
        header += sym_code + count_code

    return header


def generate_codebook_from_header(input_source: BinaryIO) -> StaticArithmeticCodebook:
    """
    iteratively generate a codebook from the input_source.

    Args:
        input_source (BinaryIO): a file that can be read in binary

    Returns:
        StaticArithmeticCodebook: codebook
    """
    bitstream = BufferedStringInput(input_source)
    codebook = OrderedDict()
    while True:

        code = bitstream.read(Settings.FIXED_CODE_SIZE)
        count = bitstream.read(Settings.ArithmeticCoding.MAX_FREQUENCY_BITSIZE)

        symbol = Settings.FIXED_SYMBOL_LOOKUP[code]
        codebook[symbol] = int(count, 2)

        if symbol == Settings.EOF_MARKER:
            return StaticArithmeticCodebook.from_counted_dataset(codebook), bitstream.flush()
