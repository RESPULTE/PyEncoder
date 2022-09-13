import collections
from typing import BinaryIO, TextIO, Dict, List

from pyencoder import Settings

from pyencoder.error import CorruptedHeaderError, CorruptedEncodingError
from pyencoder.utils.BitIO.input import BufferedStringInput
from pyencoder.utils.BitIO.output import BufferedStringOutput


from pyencoder.HuffmanCoding.StaticHuffmanCoding.codebook import generate_canonical_codebook
from pyencoder.HuffmanCoding.StaticHuffmanCoding.main import decode


def read_codelengths(bindata) -> List[int]:
    num_symbols_per_codelength = []
    for i in range(0, len(bindata), Settings.HuffmanCoding.CODELENGTH_BITSIZE):
        bin_symbol_count = bindata[i : i + Settings.HuffmanCoding.CODELENGTH_BITSIZE]
        num_symbols_per_codelength.append(int(bin_symbol_count, 2))

    if len(num_symbols_per_codelength) != Settings.HuffmanCoding.NUM_CODELENGTH:
        err_msg = "size of codelength's data ({0}) does not match default codelength's data size ({1})"
        raise CorruptedHeaderError(
            err_msg.format(len(num_symbols_per_codelength), Settings.HuffmanCoding.NUM_CODELENGTH)
        )

    return num_symbols_per_codelength


def read_symbols(bindata) -> List[str]:
    all_symbols = []
    for i in range(0, len(bindata), Settings.FIXED_CODE_SIZE):
        bin_symbol = bindata[i : i + Settings.FIXED_CODE_SIZE]
        all_symbols.append(Settings.FIXED_SYMBOL_LOOKUP[bin_symbol])

    return all_symbols


def generate_codebook_from_header(bitstream: BufferedStringInput) -> Dict[str, str]:
    bin_codelengths = bitstream.read(Settings.HuffmanCoding.CODELENGTH_BITSIZE * Settings.HuffmanCoding.NUM_CODELENGTH)
    num_symbols_per_codelength = read_codelengths(bin_codelengths)

    num_symbols = sum(num_symbols_per_codelength)
    bin_symbols = bitstream.read(num_symbols * Settings.FIXED_CODE_SIZE)
    all_symbols = read_symbols(bin_symbols)

    if len(all_symbols) != num_symbols:
        err_msg = "total decoded symbols ({0}) does not match decoded codelength's data size ({1})"
        raise CorruptedHeaderError(err_msg.format(len(all_symbols), num_symbols))

    codebook = {}
    curr_code = 0
    sym_index = 0

    for bitlength, num in enumerate(num_symbols_per_codelength, start=1):

        for _ in range(num):
            bincode = "{0:0{num}b}".format(curr_code, num=bitlength)
            codebook[bincode] = all_symbols[sym_index]
            sym_index += 1
            curr_code += 1

        curr_code <<= 1

    return codebook


def generate_header_from_codebook(codebook: Dict[str, str]) -> str:
    codelengths = [
        "0" * Settings.HuffmanCoding.CODELENGTH_BITSIZE for _ in range(Settings.HuffmanCoding.NUM_CODELENGTH)
    ]
    counted_codelengths = collections.Counter([len(code) for code in codebook.values()])

    for length, count in counted_codelengths.items():
        codelengths[length - 1] = "{0:0{bitlen}b}".format(count, bitlen=Settings.HuffmanCoding.CODELENGTH_BITSIZE)

    codelengths = "".join(codelengths)
    symbols = "".join(Settings.FIXED_CODE_LOOKUP[sym] for sym in codebook.keys())

    return codelengths + symbols


def dump(input_source: str | TextIO, output_source: BinaryIO) -> None:
    bitstream = BufferedStringOutput(output_source)

    sof_marker = Settings.FIXED_CODE_LOOKUP[Settings.SOF_MARKER]
    bitstream.write(sof_marker)

    if hasattr(input_source, "read"):
        input_source = input_source.read() + Settings.EOF_MARKER

    elif not isinstance(input_source, str):
        raise TypeError(f"Invalid type: {type(input_source).__name__}")

    codebook = generate_canonical_codebook(input_source)
    header = generate_header_from_codebook(codebook)
    bitstream.write(header)

    for symbol in input_source:
        bitstream.write(codebook[symbol])

    bitstream.flush()


def load(input_source: BinaryIO, output_source: TextIO = None) -> None | str:
    bitstream = BufferedStringInput(input_source)

    bin_sof_marker = bitstream.read(Settings.FIXED_CODE_SIZE)
    if Settings.FIXED_SYMBOL_LOOKUP[bin_sof_marker] != Settings.SOF_MARKER:
        raise CorruptedEncodingError("invalid SOF marker")

    codebook = generate_codebook_from_header(bitstream)

    if output_source:
        curr_code = ""
        to_process = bitstream

        while to_process:
            curr_code += to_process.read(1)

            if curr_code not in codebook:
                continue
            try:
                symbol = codebook[curr_code]
            except KeyError as err:
                raise CorruptedEncodingError("encoding cannot be decoded") from err

            if symbol == Settings.EOF_MARKER:
                return

            output_source.write(symbol)
            curr_code = ""

        raise EOFError("EOF not Detected")

    return decode(codebook, bitstream)
