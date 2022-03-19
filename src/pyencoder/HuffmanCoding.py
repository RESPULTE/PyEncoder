from bisect import insort_left
from collections import Counter
from typing import BinaryIO, Dict, Optional, Tuple

from bitarray import bitarray
from bitarray.util import ba2int

from pyencoder import config
from pyencoder.utils import frombin, tobin, partition_bitarray
from pyencoder.type_hints import (
    CorruptedHeaderError,
    CorruptedEncodingError,
    SupportedDataType,
    ValidDataType,
    ValidDataset,
    Bitcode,
)


def decode(header: Bitcode, encoded_data: Bitcode, dtype: ValidDataType) -> ValidDataset:
    codebook = generate_codebook_from_header(header, dtype)
    decoded_data = [None for _ in range(len(encoded_data))]

    curr_code = ""
    curr_index = 0
    for bit in encoded_data:
        curr_code += bit
        if curr_code in codebook:
            decoded_data[curr_index] = codebook[curr_code]
            curr_code = ""
            curr_index += 1

    if dtype == "s":
        decoded_data = "".join(decoded_data[:curr_index])

    return decoded_data


def generate_codebook_from_header(header: Bitcode, dtype: SupportedDataType) -> Dict[Bitcode, ValidDataType]:
    if dtype not in config.SUPPORTED_DTYPE_CODEBOOK.__members__.keys():
        raise TypeError(f"data type not supported: {dtype}")

    try:
        codelength_info = config.CODELENGTH_BITSIZE * config.MAX_CODELENGTH
        bin_codelengths, bin_symbols = header[:codelength_info], header[codelength_info:]

        num_symbols_per_codelength = [
            int(bin_codelengths[bitlen : bitlen + config.CODELENGTH_BITSIZE], 2)
            for bitlen in range(0, len(bin_codelengths), config.CODELENGTH_BITSIZE)
        ]

        num_codelength = len(num_symbols_per_codelength)
        if num_codelength != config.MAX_CODELENGTH:
            raise ValueError(
                f"number of symbols decoded({num_codelength}) does not match the default values({config.MAX_CODELENGTH})"
            )

    except Exception as err:
        raise CorruptedHeaderError(f"codelength of header cannot be decoded, error occured: {err}")

    try:
        symbols = frombin(data=bin_symbols, dtype=dtype, num=sum(num_symbols_per_codelength))
    except Exception as err:
        raise CorruptedHeaderError(f"symbols of the header cannot be decoded, error occured: {err}")

    codebook = {}
    curr_code = 0
    curr_sym_index = 0

    for bitlength, num in enumerate(num_symbols_per_codelength, start=1):

        for _ in range(num):
            bincode = tobin(curr_code, bitlength=bitlength, dtype="h")
            codebook[bincode] = symbols[curr_sym_index]
            curr_sym_index += 1
            curr_code += 1

        curr_code = curr_code << 1

    return codebook


def dump(
    dataset: ValidDataset,
    dtype: SupportedDataType,
    file: Optional[BinaryIO] = None,
    *,
    dtype_marker: bool = True,
) -> None:
    codebook, encoded_data = encode(dataset)
    header_size, codelengths, symbols = generate_header_from_codebook(codebook, dtype)

    sof_marker = tobin(config.SOF_MARKER, bitlength=config.MARKER_BITSIZE, dtype=config.MARKER_TYPE)
    eof_marker = tobin(config.EOF_MARKER, bitlength=config.MARKER_BITSIZE, dtype=config.MARKER_TYPE)

    dtype_marker_ = config.SUPPORTED_DTYPE_CODEBOOK[dtype].value if dtype_marker else ""
    datapack = bitarray(sof_marker + dtype_marker_ + header_size + codelengths + symbols + encoded_data + eof_marker)

    if file is not None:
        datapack.tofile(file)
        return

    return datapack.to01()


def load(file: BinaryIO, *, dtype: Optional[SupportedDataType] = "") -> ValidDataset:
    raw_bindata = bitarray()
    raw_bindata.frombytes(file.read())

    sof_marker = tobin(config.SOF_MARKER, bitlength=config.MARKER_BITSIZE, dtype=config.MARKER_TYPE)
    eof_marker = tobin(config.EOF_MARKER, bitlength=config.MARKER_BITSIZE, dtype=config.MARKER_TYPE)

    try:
        raw_bindata = partition_bitarray(raw_bindata, delimiter=[sof_marker, eof_marker])[1]

        if not dtype:
            encoding_dtype, header_size, huffman_data = partition_bitarray(
                raw_bindata, index=[config.DTYPE_MARKER_BITSIZE, config.HEADER_MARKER_BITSIZE], continuous=True
            )
            encoding_dtype = config.SUPPORTED_DTYPE_CODEBOOK(encoding_dtype.to01()).name

        else:
            header_size, huffman_data = partition_bitarray(raw_bindata, index=config.HEADER_MARKER_BITSIZE)
            encoding_dtype = dtype

        header, encoded_data = partition_bitarray(huffman_data, index=ba2int(header_size))

        data_to_decode = {
            "header": header.to01(),
            "encoded_data": encoded_data.to01(),
            "dtype": encoding_dtype,
        }

        return decode(**data_to_decode)

    except Exception as err:
        raise CorruptedEncodingError(f"encoding cannot be decoded, error occured: {err}")


def generate_header_from_codebook(codebook: Dict[ValidDataType, Bitcode], dtype: str) -> Tuple[Bitcode, Bitcode]:
    codelengths = ["0" * config.CODELENGTH_BITSIZE for _ in range(0, config.MAX_CODELENGTH)]
    counted_codelengths = Counter([len(code) for code in codebook.values()])

    for length, count in counted_codelengths.items():
        codelengths[length - 1] = tobin(data=count, bitlength=config.CODELENGTH_BITSIZE, dtype="h")

    codelengths = "".join(codelengths)
    symbols = tobin(list(codebook.keys()), dtype=dtype)
    header_size = tobin(len(codelengths + symbols), bitlength=config.HEADER_MARKER_BITSIZE, dtype="i")

    return header_size, codelengths, symbols


def encode(dataset: ValidDataset) -> Tuple[Dict[ValidDataType, Tuple[Bitcode, int]], Bitcode, Bitcode]:
    # putting the symbol in a list to allow concatenation for 'int' and 'float' during the 'tree building process'
    to_process = [([[symbol], count]) for symbol, count in Counter(dataset).most_common()]
    codebook = {symbol[0]: 0 for symbol, _ in to_process}

    # building the huffman tree
    while len(to_process) != 1:
        (symbol_1, count_1), (symbol_2, count_2) = to_process[:-3:-1]

        to_process = to_process[:-2]

        # insert the newly formed subtree back into the list
        # PS: not so sure why i added the sort key with a negative for its frequency
        #     but the entire process fails without it so.... yeea :/
        insort_left(
            to_process,
            (symbol_1 + symbol_2, count_1 + count_2),
            key=lambda data: -data[1],
        )

        # for every element/symbol in the subtree, plus 1 for their code length
        for sym_1 in symbol_1:
            codebook[sym_1] += 1
        for sym_2 in symbol_2:
            codebook[sym_2] += 1

    # just to ensure that the very first value will be zero
    curr_code = -1

    # making sure that the bit shift won't ever happen for the first value
    prev_bitlength = float("inf")

    canonical_codebook = {}

    # sort the codebook by the bitlength
    to_process = sorted([(bitlength, symbol) for symbol, bitlength in codebook.items()])

    for bitlength, symbol in to_process:

        # increment the code, which is in integer form btw, by 1
        # if the bitlength of this symbol is more than the last symbol, left-shift the code using bitwise operation
        curr_code += 1
        if bitlength > prev_bitlength:
            curr_code = curr_code << bitlength - prev_bitlength

        canonical_codebook[symbol] = tobin(curr_code, bitlength=bitlength, dtype="i")
        prev_bitlength = bitlength

    # the actual encoding process for the data
    encoded_data = "".join([canonical_codebook[data] for data in dataset])

    # marker to indicate the size of the encoded data
    return canonical_codebook, encoded_data


with open("f", "wb") as f:
    dump("112211222454", "s", f)

with open("f", "rb") as f:
    print(load(f))
