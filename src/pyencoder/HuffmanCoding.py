from bisect import insort
from collections import Counter
from typing import BinaryIO, Dict, Tuple, Type, Union

from bitarray import bitarray
from bitarray.util import ba2int

from pyencoder.utils import frombin, tobin, partition_bitarray
from pyencoder.type_hints import (
    SupportedDataType,
    ValidDataType,
    ValidDataset,
    Bitcode,
)
from pyencoder.config import (
    MARKER,
    MARKER_DTYPE,
    MARKER_SIZE,
    MAX_CODELENGTH,
    CODELENGTH_BITSIZE,
    SUPPORTED_DTYPE_CODEBOOK,
    ENCODED_DATA_MARKER_SIZE,
    HEADER_MARKER_SIZE,
    DTYPE_MARKER_SIZE,
)


def decode(header: str, encoded_data: str, dtype: ValidDataType) -> ValidDataset:
    codebook = generate_codebook_from_header(header, dtype)
    decoded_data = []

    curr_code = ""
    for bit in encoded_data:
        curr_code += bit
        if curr_code in codebook:
            decoded_data.append(codebook[curr_code])
            curr_code = ""

    if dtype == "s":
        decoded_data = "".join(decoded_data)

    return decoded_data


def generate_codebook_from_header(header: Bitcode, dtype: Type) -> Dict[Bitcode, Union[str, int, float]]:
    codelength_info = CODELENGTH_BITSIZE * MAX_CODELENGTH
    bin_codelengths, bin_symbols = header[:codelength_info], header[codelength_info:]

    num_symbols = [
        int(bin_codelengths[bitlen : bitlen + CODELENGTH_BITSIZE], 2)
        for bitlen in range(0, len(bin_codelengths), CODELENGTH_BITSIZE)
    ]
    symbols = frombin(data=bin_symbols, dtype=dtype, num=sum(num_symbols))

    codebook = {}
    curr_code = 0
    curr_sym_index = 0

    for bitlength, num in enumerate(num_symbols, start=1):

        for _ in range(num):
            bincode = tobin(curr_code, bitlength=bitlength, dtype="h")
            codebook[bincode] = symbols[curr_sym_index]
            curr_sym_index += 1
            curr_code += 1

        curr_code = curr_code << 1

    return codebook


def dump(
    dataset: ValidDataset,
    file: BinaryIO,
    dtype: SupportedDataType,
    *,
    marker: ValidDataType = MARKER,
    marker_size: int = MARKER_SIZE
) -> None:
    marker = tobin(marker, bitlength=marker_size, dtype=MARKER_DTYPE)

    codebook, encoded_data = encode(dataset)
    header = generate_header_from_codebook(codebook, dtype)

    datapack = bitarray(marker + header + encoded_data)
    datapack.tofile(file)


def load(file: BinaryIO, marker: ValidDataType = MARKER, marker_size: int = MARKER_SIZE) -> ValidDataset:
    raw_bindata = bitarray()
    raw_bindata.frombytes(file.read())

    bin_marker = tobin(marker, bitlength=marker_size, dtype=MARKER_DTYPE)
    _, raw_bindata = partition_bitarray(raw_bindata, delimiter=bin_marker)

    header_size, huffman_data = partition_bitarray(raw_bindata, index=[HEADER_MARKER_SIZE])

    dtype, header, encoding_size, encoded_data = partition_bitarray(
        huffman_data, index=[DTYPE_MARKER_SIZE, ba2int(header_size), ENCODED_DATA_MARKER_SIZE], continuous=True
    )

    data_to_decode = {
        "header": header.to01(),
        "encoded_data": encoded_data[: ba2int(encoding_size)].to01(),
        "dtype": SUPPORTED_DTYPE_CODEBOOK(dtype.to01()).name,
    }

    return decode(**data_to_decode)


def generate_header_from_codebook(codebook: Dict[Union[str, int, float], Bitcode], dtype: Type = str) -> Bitcode:
    codelengths = ["0" * CODELENGTH_BITSIZE for _ in range(0, MAX_CODELENGTH)]
    counted_codelengths = Counter([len(code) for code in codebook.values()])

    for length, count in counted_codelengths.items():
        codelengths[length - 1] = tobin(data=count, bitlength=8, dtype="h")

    symbols = tobin(list(codebook.keys()), dtype=dtype)
    header = "".join(codelengths) + symbols
    header_size = tobin(len(header), bitlength=HEADER_MARKER_SIZE, dtype="i")

    return header_size + SUPPORTED_DTYPE_CODEBOOK[dtype].value + header


def encode(dataset: ValidDataset) -> Tuple[Dict[Union[str, int, float], Tuple[Bitcode, int]], Bitcode]:
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
        insort(
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

        canonical_codebook[symbol] = tobin(curr_code, bitlength=bitlength, dtype="h")
        prev_bitlength = bitlength

    # the actual encoding process for the data
    encoded_data = "".join([canonical_codebook[data] for data in dataset])

    # marker to indicate the size of the encoded data
    encoded_data_size = tobin(len(encoded_data), bitlength=ENCODED_DATA_MARKER_SIZE, dtype="i")

    encoding = encoded_data_size + encoded_data

    return canonical_codebook, encoding


# s = "Lorem Ipsum is simply dummy text of the printing and typesetting industry. Lorem Ipsum has been the industry's standard dummy text ever since the 1500s, when an unknown printer took a galley of type and scrambled it to make a type specimen book. It has survived not only five centuries, but also the leap into electronic typesetting, remaining essentially unchanged. It was popularised in the 1960s with the release of Letraset sheets containing Lorem Ipsum passages, and more recently with desktop publishing software like Aldus PageMaker including versions of Lorem Ipsum."
# s = [1, 2, 3, 4, 5]
# with open("f", "wb") as f:
#     dump(s, f, "h")

# with open("f", "rb") as f:
#     print(load(f) == s)
