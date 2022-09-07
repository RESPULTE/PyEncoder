import collections
from typing import BinaryIO, TextIO, Tuple, Dict, List

from pyencoder import Config

from pyencoder.type_hints import CorruptedHeaderError, CorruptedEncodingError
from pyencoder.utils.BitIO import BufferedBitOutput, BufferedBitInput
from pyencoder.utils.BitIO.input import BufferedStringInput
from pyencoder.HuffmanCoding import Settings

from pyencoder.HuffmanCoding.StaticHuffmanCoding.codebook import generate_canonical_codebook
from pyencoder.HuffmanCoding.StaticHuffmanCoding.main import decode


def read_codelengths(bindata) -> List[int]:
    num_symbols_per_codelength = []
    for i in range(0, len(bindata), Settings.CODELENGTH_BITSIZE):
        bin_symbol_count = bindata[i : i + Settings.CODELENGTH_BITSIZE]
        num_symbols_per_codelength.append(int(bin_symbol_count, 2))

    return num_symbols_per_codelength


def read_symbols(bindata) -> List[str]:
    all_symbols = []
    for i in range(0, len(bindata), Settings.SYMBOL_BITSIZE):
        bin_symbol = bindata[i : i + Settings.SYMBOL_BITSIZE]
        all_symbols.append(chr(int(bin_symbol, 2)))

    return all_symbols


def generate_codebook_from_header(bitstream: BufferedStringInput) -> Dict[str, str]:
    bin_codelengths = bitstream.read(Settings.CODELENGTH_BITSIZE * Settings.MAX_CODELENGTH)
    num_symbols_per_codelength = read_codelengths(bin_codelengths)

    if len(num_symbols_per_codelength) != Settings.MAX_CODELENGTH:
        err_msg = "size of codelength's data ({0}) does not match default codelength's data size ({1})"
        raise CorruptedHeaderError(err_msg.format(len(num_symbols_per_codelength), Settings.MAX_CODELENGTH))

    num_symbols = sum(num_symbols_per_codelength)
    bin_symbols = bitstream.read(num_symbols * Settings.SYMBOL_BITSIZE)
    all_symbols = read_symbols(bin_symbols)

    if len(all_symbols) != num_symbols:
        err_msg = "total decoded symbols ({0}) does not match decoded codelength's data size ({1})"
        raise CorruptedHeaderError(err_msg.format({len(all_symbols)}, num_symbols))

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
    codelengths = ["0" * Settings.CODELENGTH_BITSIZE for _ in range(Settings.MAX_CODELENGTH)]
    counted_codelengths = collections.Counter([len(code) for code in codebook.values()])

    for length, count in counted_codelengths.items():
        codelengths[length - 1] = "{0:0{bitlen}b}".format(count, bitlen=Settings.CODELENGTH_BITSIZE)

    codelengths = "".join(codelengths)
    symbols = "".join("{0:0{num}b}".format(ord(sym), num=Settings.SYMBOL_BITSIZE) for sym in codebook.keys())

    return codelengths + symbols


def dump(input_source: str | TextIO, output_source: BinaryIO) -> None:
    bitstream = BufferedBitOutput(output_source)

    sof_marker = "{0:0{num}b}".format(ord(Config["SOF_MARKER"]), num=Settings.SYMBOL_BITSIZE)
    bitstream.write(sof_marker)

    if not isinstance(input_source, str):
        try:
            input_source = input_source.read() + Config["EOF_MARKER"]
        except AttributeError as err:
            raise TypeError(f"Invalid input source: {type(input_source).__name__}") from err

    codebook = generate_canonical_codebook(input_source)
    header = generate_header_from_codebook(codebook)
    bitstream.write(header)

    for symbol in input_source:
        bitstream.write(codebook[symbol])

    bitstream.flush()


def load(input_source: BinaryIO, output_source: TextIO = None) -> None | str:
    bitstream = BufferedBitInput(input_source)

    bin_sof_marker = bitstream.read(Settings.SYMBOL_BITSIZE)
    if chr(int(bin_sof_marker, 2)) != Config["SOF_MARKER"]:
        raise CorruptedEncodingError("invalid SOF marker")

    codebook = generate_codebook_from_header(bitstream)

    if output_source:
        curr_code = ""
        to_process = bitstream

        while to_process:
            curr_code += to_process.read(1)

            if curr_code not in codebook:
                continue

            symbol = codebook[curr_code]

            if symbol == Config["EOF_MARKER"]:
                return

            output_source.write(symbol)
            curr_code = ""

        raise CorruptedEncodingError("EOF not Detected")

    return decode(codebook, bitstream)
