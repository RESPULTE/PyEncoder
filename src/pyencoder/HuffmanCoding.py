from typing import BinaryIO, Dict, List, Tuple, Type, Union
from collections import Counter, OrderedDict
from bisect import insort

from bitarray import bitarray
from bitarray.util import ba2int

from pyencoder.utils import frombin, tobin, partition_bitarray
from pyencoder._type_hints import (
    CorruptedHeaderError,
    CorruptedDataError,
    ValidDataType,
    ValidDataset,
    Bitcode,
)
from pyencoder.config import (
    ENCODING_MARKER,
    _SUPPORTED_DTYPE_FROM_BIN,
    _SUPPORTED_DTYPE_TO_BIN,
    _ENCODING_MARKER_SIZE,
    _HEADER_MARKER_SIZE,
    _DTYPE_MARKER_SIZE,
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

    if dtype == str:
        decoded_data = "".join(decoded_data)

    return decoded_data


def generate_codebook_from_header(header: Bitcode, dtype: Type) -> OrderedDict[Bitcode, Union[str, int, float]]:
    raw_bitlengths, raw_symbols = header[: 8 * 16], header[8 * 16 :]
    num_symbols = [int(raw_bitlengths[bitlen : bitlen + 8], 2) for bitlen in range(0, len(raw_bitlengths), 8)]
    symbols = [frombin(raw_symbols[bitlen : bitlen + 8], dtype) for bitlen in range(0, len(raw_symbols), 8)]

    codebook = {}
    curr_code = 0
    curr_sym_index = 0

    for bitlength, num in enumerate(num_symbols, start=1):

        for _ in range(num):
            bincode = tobin(curr_code, bitlength=bitlength, dtype=int)
            codebook[bincode] = symbols[curr_sym_index]
            curr_sym_index += 1
            curr_code += 1

        curr_code = curr_code << 1

    return codebook


def dump(dataset: ValidDataset, file: BinaryIO, marker: ValidDataType = None) -> None:
    """
    encode the given dataset with Huffman Coding and write it to a file in binary

    Args:
        dataset (ValidDataset): a dataset of type string, list of integer / float

        file (BinaryIO): an file object opened in the 'wb' (write in binary) mode

        decimal (int, optional):  will be used for the float to binary conversion if the datatype given is float. Defaults to 2.

        delimiter (int, optional): used to seperate the header and the encoded data.
                                   if None is given, a random unicode character of my selection will be used instead

        marker (int, optional): used to mark the beginning of the huffman coding.
                                if None is given, a random unicode character of my selection will be used instead

    """
    marker = tobin(marker or ENCODING_MARKER, bitlength=16)

    codebook, encoded_data, dtype = encode(dataset)

    header = generate_header_from_codebook(codebook, dtype)

    # the actual data
    huffman_data = header + encoded_data

    # the size of the entire huffmancoding
    huffmancoding_size = tobin(len(huffman_data), bitlength=_ENCODING_MARKER_SIZE)

    datapack = bitarray(marker + huffmancoding_size + huffman_data)

    datapack.tofile(file)


def load(file: BinaryIO, marker: ValidDataType = None) -> ValidDataset:
    """
    load the huffman coding from a binary file an decodes it

    Args:
        file (BinaryIO): an file object opened in the 'rb' (read in binary) mode

        delimiter (int, optional): used to seperate the header and the encoded data.
                                   if None is given, a random unicode character of my selection will be used instead

        marker (int, optional): used to mark the beginning of the huffman coding.
                                if None is given, a random unicode character of my selection will be used instead

    Raises:
        DecompressionError: if any error occurs during the decoding process

    Returns:
        ValidDataset: the decoded data
    """
    encoded_huffdata = bitarray()
    encoded_huffdata.frombytes(file.read())

    _, encoded_huffdata = partition_bitarray(encoded_huffdata, delimiter=tobin(marker or ENCODING_MARKER, 16))

    huffmancoding_size = ba2int(encoded_huffdata[:_ENCODING_MARKER_SIZE])

    huffman_data = encoded_huffdata[_ENCODING_MARKER_SIZE : _ENCODING_MARKER_SIZE + huffmancoding_size]

    header_size, huffman_data = ba2int(huffman_data[:_HEADER_MARKER_SIZE]), huffman_data[_HEADER_MARKER_SIZE:]
    raw_header, encoded_data = huffman_data[:header_size], huffman_data[header_size:]

    dtype, header = raw_header[:_DTYPE_MARKER_SIZE], raw_header[_DTYPE_MARKER_SIZE:]

    data_to_decode = {
        "header": header.to01(),
        "encoded_data": encoded_data.to01(),
        "dtype": _SUPPORTED_DTYPE_FROM_BIN[dtype.to01()],
    }

    return decode(**data_to_decode)


def generate_header_from_codebook(codebook: OrderedDict[Union[str, int, float], Bitcode], dtype: Type = str) -> Bitcode:
    codebook = list(codebook.items()) + [("?", "")]
    bitlengths: List[Bitcode] = ["0" * 8 for _ in range(0, 16)]
    symbols: List[Bitcode] = []

    curr_code_sum = 0
    prev_bitlength = 1
    for symbol, huffcode in codebook:

        symbols.append(tobin(symbol, dtype=dtype))

        curr_bitlength = len(huffcode)
        if curr_bitlength != prev_bitlength:
            bitlengths[prev_bitlength - 1] = tobin(data=curr_code_sum, bitlength=8, dtype=int)
            prev_bitlength = curr_bitlength
            curr_code_sum = 0

        curr_code_sum += 1

    header = _SUPPORTED_DTYPE_TO_BIN[dtype] + "".join(bitlengths + symbols[:-1])
    return tobin(len(header), bitlength=_HEADER_MARKER_SIZE) + header


def encode(dataset: ValidDataset) -> Tuple[Dict[Union[str, int, float], Tuple[Bitcode, int]], Bitcode]:
    if isinstance(dataset, str):
        dtype = str

    elif all(isinstance(data, int) for data in dataset):
        dtype = int

    else:
        try:
            dataset = [float(data) for data in dataset]

        except TypeError:
            raise TypeError("inconsistent data type in dataset")

        else:
            dtype = float

    counted_dataset = [([symbol], count) for symbol, count in Counter(dataset).most_common()]
    codebook = {symbol[0]: 0 for symbol, _ in counted_dataset}

    while len(counted_dataset) != 1:
        (symbol_1, count_1), (symbol_2, count_2) = counted_dataset[:-3:-1]

        counted_dataset = counted_dataset[:-2]

        insort(
            counted_dataset,
            (symbol_1 + symbol_2, count_1 + count_2),
            key=lambda data: -data[1],
        )

        for sym_1 in symbol_1:
            codebook[sym_1] += 1
        for sym_2 in symbol_2:
            codebook[sym_2] += 1

    curr_code = -1
    prev_bitlength = float("inf")
    canonical_codebook = OrderedDict()
    code_list = sorted([(bitlength, symbol) for symbol, bitlength in codebook.items()])

    for bitlength, symbol in code_list:

        curr_code += 1
        if bitlength > prev_bitlength:
            curr_code = curr_code << bitlength - prev_bitlength

        canonical_codebook[symbol] = tobin(curr_code, bitlength, int)
        prev_bitlength = bitlength

    return canonical_codebook, "".join([canonical_codebook[data] for data in dataset]), dtype


# TODO: a new dump function, with optional dtype indicator, optional codebook parameter
# ? set every constant as optional arguement -> will have to pass it to each related functions
