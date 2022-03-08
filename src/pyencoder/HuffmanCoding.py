from re import U
from typing import BinaryIO, Callable, Dict, List, Optional, Tuple, Type, Union
from collections import Counter, namedtuple, OrderedDict
from functools import partial
from bisect import insort

from bitarray import bitarray
from bitarray.util import ba2int

from pyencoder.utils import frombin, tobin, partition_bitarray
from pyencoder._type_hints import (
    CorruptedHeaderError,
    CorruptedDataError,
    ValidDataType,
    ValidDataset,
    BitCode,
)
from pyencoder.config import (
    ENCODING_MARKER,
    _SUPPORTED_DTYPE_FROM_BIN,
    _SUPPORTED_DTYPE_TO_BIN,
    _ENCODING_MARKER_SIZE,
    _DECIMAL_MARKER_SIZE,
    _HEADER_MARKER_SIZE,
    _DTYPE_MARKER_SIZE,
    _ELEM_MARKER_SIZE,
    _MAX_DECIMAL,
)


Huffcode = namedtuple("Huffcode", ["bitcode", "bitlength"])

'''

def decode(
    huffman_string: str, encoded_data: str, data_size: int, dtype: ValidDataType, *, decimal: int = 2
) -> ValidDataset:
    """
    decode the Huffman Coding string into the given data type

    Args:
        huffman_string (str): a binary representation of the huffman tree

        encoded_data (str): a binary encoded data

        data_size (int): the size of each actual data is in the binary representation of the huffman tree

        dtype (ValidDataset): data type to decode into

        decimal (int, optional): will be used for the float to binary conversion if the datatype given is float. Defaults to 2.

    Raises:
        DecompressionError: if any error occurs during the decoding process

    Returns:
        ValidDataset: decoded data in the given dataset
    """
    bindecoder_config = {
        str: {"dtype": str},
        int: {"signed": True, "dtype": int},
        float: {"decimal": decimal, "signed": True, "dtype": float},
    }
    bindecoder = partial(frombin, **bindecoder_config[dtype])
    huffman_tree = build_tree_from_huffmanstring(huffman_string, data_size, bindecoder)
    catalogue = generate_catalogue(huffman_tree)

    try:
        current_node = huffman_tree
        decoded_data = []
        curr_tag = ""

        for tag in encoded_data:

            current_node = current_node.left if tag == "0" else current_node.right

            curr_tag += tag
            if not isinstance(current_node, Huffman_Node):
                decoded_data.append(catalogue[curr_tag])
                current_node = huffman_tree
                curr_tag = ""
                continue

    except Exception as e:
        raise CorruptedDataError(f"encoded huffman data is unusable, error occured -> {e}")

    else:
        return "".join(decoded_data) if dtype == str else decoded_data

'''


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
    marker = tobin(marker or ENCODING_MARKER)

    header, encoded_data = encode(dataset)

    header = format(len(header), f"0{_HEADER_MARKER_SIZE}b") + header

    # the actual data
    huffman_data = header + encoded_data

    # the size of the entire huffmancoding
    huffmancoding_size = format(len(huffman_data), f"0{_ENCODING_MARKER_SIZE}b")

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

    _, encoded_huffdata = partition_bitarray(encoded_huffdata, tobin(marker or ENCODING_MARKER))

    huffmancoding_size = ba2int(encoded_huffdata[:_ENCODING_MARKER_SIZE])

    huffman_data = encoded_huffdata[_ENCODING_MARKER_SIZE : _ENCODING_MARKER_SIZE + huffmancoding_size]

    header_len, huffman_data = partition_bitarray(huffman_data, index=_HEADER_MARKER_SIZE)

    header, encoded_data = partition_bitarray(huffman_data, index=ba2int(header_len))

    dtype, huffman_string = partition_bitarray(header, index=_DTYPE_MARKER_SIZE)

    data_size, huffman_string = partition_bitarray(huffman_string, index=_ELEM_MARKER_SIZE)

    data_to_decode = {
        "huffman_string": huffman_string.to01(),
        "encoded_data": encoded_data.to01(),
        "data_size": ba2int(data_size),
        "dtype": _SUPPORTED_DTYPE_FROM_BIN[dtype.to01()],
    }

    if data_to_decode["dtype"] == float:
        decimal, huffman_string = partition_bitarray(huffman_string, index=_DECIMAL_MARKER_SIZE)
        data_to_decode.update(decimal=ba2int(decimal), huffman_string=huffman_string.to01())

    # return decode(**data_to_decode)


def generate_header(canonical_codebook: OrderedDict[Union[str, int, float], Huffcode], dtype: Type = str) -> BitCode:
    bitlengths: List[BitCode] = ["0" * 8 for _ in range(0, 16 - 1)]
    symbols: List[BitCode] = []

    curr_code_sum = 0
    curr_bitlength = 1
    for symbol, huffcode in canonical_codebook.items():

        if huffcode.bitlength != curr_bitlength:
            bitlengths[curr_bitlength] = tobin(curr_code_sum)
            curr_bitlength = huffcode.bitlength
            curr_code_sum = 0

        symbols.append(tobin(symbol))
        curr_code_sum += 1

    return "".join(_SUPPORTED_DTYPE_TO_BIN[dtype] + bitlengths + symbols)


def encode(dataset: ValidDataset) -> Tuple[Dict[Union[str, int, float], Huffcode], BitCode]:
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

    code_list = sorted([(bitlength, symbol) for symbol, bitlength in codebook.items()])

    curr_code = -1
    prev_bitlength = float("inf")
    canonical_codebook: "OrderedDict[ValidDataType, Huffcode]" = OrderedDict()

    for bitlength, symbol in code_list:

        new_code = curr_code + 1
        if bitlength > prev_bitlength:
            new_code = new_code << bitlength - prev_bitlength

        canonical_codebook[symbol] = Huffcode(tobin(new_code, bitlength, dtype), bitlength)
        prev_bitlength = bitlength
        curr_code = new_code

    return canonical_codebook, "".join([canonical_codebook[data].bitcode for data in dataset])


# TODO: a new dump function, with optional dtype indicator, optional codebook parameter
# ? set every constant as optional arguement -> will have to pass it to each related functions
