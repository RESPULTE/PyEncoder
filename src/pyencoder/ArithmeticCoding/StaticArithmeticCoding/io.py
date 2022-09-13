from collections import OrderedDict
from typing import BinaryIO, TextIO

from pyencoder import Settings
from pyencoder.utils.BitIO.input import BufferedStringInput

from pyencoder.ArithmeticCoding.StaticArithmeticCoding.main import decode, encode
from pyencoder.ArithmeticCoding.StaticArithmeticCoding.codebook import ArithmeticCodebook


def load(input_file: BinaryIO, output_file: TextIO | None) -> None | str:
    codebook, leftover_bits = generate_codebook_from_header(input_file)

    encoded_data: str = "{0:0b}".format(int.from_bytes(input_file.read(), Settings.ENDIAN))

    encoded_data = encoded_data.rjust(8 * -(-len(encoded_data) // 8), "0")
    decoded_data = decode(codebook, leftover_bits + encoded_data)
    if not output_file:
        return decoded_data

    output_file.write("".join(decoded_data))


def dump(input_file: TextIO | str, output_file: BinaryIO) -> None:
    data = input_file.read() if hasattr(input_file, "read") else input_file
    codebook, encoded_data = encode(data)
    header = generate_header_from_codebook(codebook)

    if not output_file:
        return header + encoded_data

    data = header + encoded_data

    size = len(data)
    data = data.ljust(8 * -(-size // 8), "0")

    bytes_to_output = int.to_bytes(int(data, 2), -(-size // 8), Settings.ENDIAN)
    output_file.write(bytes_to_output)


def generate_header_from_codebook(codebook: ArithmeticCodebook) -> str:
    header = ""

    for sym, (sym_low, sym_high) in codebook.items():
        sym_code = Settings.FIXED_CODE_LOOKUP[sym]
        count_code = "{0:0{num}b}".format(sym_high - sym_low, num=Settings.ArithmeticCoding.MAX_FREQUENCY_BITSIZE)
        header += sym_code + count_code

    return header


def generate_codebook_from_header(input_file: BinaryIO) -> ArithmeticCodebook:
    # if chr(bitstream.read(Config["SYMBOL_BITSIZE"])) != Config["SOF_MARKER"]:
    #     raise Exception("SOF not detected")
    bitstream = BufferedStringInput(input_file)
    codebook = OrderedDict()
    while True:

        code = bitstream.read(Settings.FIXED_CODE_SIZE)
        count = bitstream.read(Settings.ArithmeticCoding.MAX_FREQUENCY_BITSIZE)

        symbol = Settings.FIXED_SYMBOL_LOOKUP[code]
        codebook[symbol] = int(count, 2)

        if symbol == Settings.EOF_MARKER:
            return ArithmeticCodebook.from_counted_dataset(codebook), bitstream.flush()
