from collections import OrderedDict
from typing import BinaryIO, TextIO

from pyencoder import Settings
from pyencoder.utils.BitIO.input import BufferedStringInput
from pyencoder.utils.BitIO.output import BufferedStringOutput

from pyencoder.ArithmeticCoding.StaticArithmeticCoding.main import decode, encode
from pyencoder.ArithmeticCoding.StaticArithmeticCoding.codebook import ArithmeticCodebook


def load(input_file: BinaryIO, output_file: TextIO | None) -> None | str:
    data = BufferedStringInput(input_file)

    codebook = generate_codebook_from_header(data)

    decoded_data = decode(codebook, input_file.read())
    if not output_file:
        return decoded_data

    output_file.write("".join(decoded_data))


def dump(input_file: TextIO | str, output_file: BinaryIO) -> None:
    data = input_file.read() if hasattr(input_file, "read") else input_file
    codebook, encoded_data = encode(data)
    header = generate_header_from_codebook(codebook)

    if not output_file:
        return header + encoded_data

    bitstream = BufferedStringOutput(output_file)
    bitstream.write(header + encoded_data)
    bitstream.flush()


def generate_header_from_codebook(codebook: ArithmeticCodebook) -> str:
    header = ""

    for sym, (sym_low, sym_high) in codebook.items():
        sym_code = Settings.FIXED_CODE_LOOKUP[sym]
        count_code = "{0:0{num}b}".format(sym_high - sym_low, num=Settings.ArithmeticCoding.MAX_FREQUENCY.bit_length())

        header += sym_code + count_code

    return header


def generate_codebook_from_header(bitstream: BufferedStringInput) -> ArithmeticCodebook:
    # if chr(bitstream.read(Config["SYMBOL_BITSIZE"])) != Config["SOF_MARKER"]:
    #     raise Exception("SOF not detected")

    codebook = OrderedDict()
    while True:

        code = bitstream.read(Settings.FIXED_CODE_SIZE)
        count = bitstream.read(Settings.ArithmeticCoding.MAX_FREQUENCY.bit_length())

        symbol = Settings.FIXED_SYMBOL_LOOKUP[code]
        codebook[symbol] = int(count, 2)

        if symbol == Settings.EOF_MARKER:
            return ArithmeticCodebook.from_counted_dataset(codebook)
