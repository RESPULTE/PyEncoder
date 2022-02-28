from bisect import insort
from functools import partial
from collections import Counter
from dataclasses import dataclass
from typing import BinaryIO, Callable, Dict, List, Tuple, Union

from bitarray import bitarray
from bitarray.util import ba2int

from pyencoder._type_hints import BinaryCode, DecompressionError, ValidDataType
from pyencoder.config import (
    _DTYPEMARKER_LEN,
    _DATASIZEMARKER_LEN,
    _DATA_BINARYSIZE_MARKER_LEN,
    _SUPPORTED_DTYPE_FROM_BIN,
    _SUPPORTED_DTYPE_TO_BIN,
    DELIMITER,
    HUFFMARKER,
    _DECIMAL_MARKER_LEN,
)
from pyencoder.utils import frombin, tobin


@dataclass(frozen=True, slots=True)
class Huffman_Node:

    left: Union["Huffman_Node", str]
    right: Union["Huffman_Node", str]


def encode(dataset: Union[str, list, tuple], dtype: ValidDataType, *, decimal: int = 2) -> Tuple[str, str]:
    # encoding the data
    huffman_tree = _build_tree_from_dataset(Counter(dataset).most_common())
    catalogue = {v: k for k, v in _generate_catalogue(huffman_tree).items()}
    encoded_data = _encode_dataset(dataset, catalogue)

    # generating the string repr of the huffman tree
    try:
        binencoder_config = {
            str: {"dtype": str},
            int: {"signed": True, "dtype": int},
            float: {"decimal": decimal, "signed": True, "dtype": float},
        }
        binencoder = partial(tobin, **binencoder_config[dtype])
        huffman_string = _generate_huffmanstring(huffman_tree, binencoder)
    except Exception:
        raise TypeError("inconsistent data type")

    return huffman_string, encoded_data


def _encode_dataset(dataset: ValidDataType, catalogue: Dict[BinaryCode, ValidDataType]) -> BinaryCode:
    if isinstance(dataset, str):
        dataset = list(dataset)
    return "".join([catalogue[data] for data in dataset])


def _generate_huffmanstring(huffman_tree: Huffman_Node, binencoder: Callable) -> List[str]:
    def traverse_huffmantree(huffman_tree: Huffman_Node, max_bitsize: int) -> List[str]:
        if not isinstance(huffman_tree, Huffman_Node):
            bindata = binencoder(huffman_tree)
            bindatalen = len(bindata)
            if bindatalen > max_bitsize[0]:
                max_bitsize[0] = bindatalen

            return ["0", bindata]

        huffmanString = ["1"]
        for node in [huffman_tree.left, huffman_tree.right]:
            huffmanString.extend(traverse_huffmantree(node, max_bitsize))

        return huffmanString

    max_bitsize = [0]
    huffman_list = traverse_huffmantree(huffman_tree, max_bitsize)
    max_bitsize = max_bitsize[0]

    for index, data in enumerate(huffman_list):
        if huffman_list[index - 1] == "0":
            huffman_list[index] = data[0] + data[1:].zfill(max_bitsize - 1)

    huffman_list.insert(0, format(max_bitsize, f"0{_DATA_BINARYSIZE_MARKER_LEN}b"))

    return "".join(huffman_list)


def decode(
    huffman_string: str, encoded_data: str, data_size: int, dtype: ValidDataType, *, decimal: int = 2
) -> ValidDataType:
    try:
        bindecoder_config = {
            str: {"dtype": str},
            int: {"signed": True, "dtype": int},
            float: {"decimal": decimal, "signed": True, "dtype": float},
        }
        bindecoder = partial(frombin, **bindecoder_config[dtype])
        huffman_tree = _build_tree_from_bitarray(huffman_string, data_size, bindecoder)
        catalogue = _generate_catalogue(huffman_tree)

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
        raise DecompressionError(f"Unknown error has occured -> {e}")

    else:
        return "".join(decoded_data) if dtype == str else decoded_data


def dump(
    dataset: Union[str, list, tuple], file: BinaryIO, *, decimal: int = 2, delimiter: int = None, marker: int = None
) -> None:
    if delimiter or marker and delimiter == marker:
        raise ValueError("delimiter and huff marker should not be the same")

    if isinstance(dataset, str):
        dtype = str
    elif all(isinstance(data, int) for data in dataset):
        dtype = int
    elif all(isinstance(data, (int, float)) for data in dataset):
        dtype = float
    else:
        raise ValueError("inconsistent datatype in dataset")

    delimiter = tobin(delimiter if delimiter else DELIMITER, str)
    marker = tobin(marker if marker else HUFFMARKER, str)

    header, encoded_data = encode(dataset, dtype, decimal=decimal)

    if dtype == float:
        decimal_marker = format(decimal, f"0{_DECIMAL_MARKER_LEN}b")
        header = list(header)
        header[_DATA_BINARYSIZE_MARKER_LEN:_DATA_BINARYSIZE_MARKER_LEN] = decimal_marker
        header = "".join(header)

    # the actual data
    huffman_data = header + delimiter + encoded_data

    dtype_marker = _SUPPORTED_DTYPE_TO_BIN[dtype]

    # the size of the entire huffmancoding
    huffmancoding_size = format(len(huffman_data), f"0{_DATASIZEMARKER_LEN}b")

    datapack = bitarray(marker + dtype_marker + huffmancoding_size + huffman_data)

    datapack.tofile(file)


def load(file: BinaryIO, *, delimiter: str = None, marker: str = None) -> ValidDataType:
    if delimiter or marker and delimiter == marker:
        raise ValueError("delimiter and huff marker should not be the same")

    marker = tobin(marker if marker else HUFFMARKER, str)
    delimiter = tobin(delimiter if delimiter else DELIMITER, str)

    try:
        encoded_data = bitarray()
        encoded_data.frombytes(file.read())

        _, encoded_data = partition_bitstring(encoded_data, marker)

        # get the data type of the encoded data
        encoded_dtype = _SUPPORTED_DTYPE_FROM_BIN[encoded_data[:_DTYPEMARKER_LEN].to01()]

        # get the index where the actual encoded data (including the header) starts
        # get the starting and ending index of the datasize indicator
        data_starting_index = datasize_ending_index = _DATASIZEMARKER_LEN + _DTYPEMARKER_LEN
        datasize_starting_index = _DTYPEMARKER_LEN

        data_size = ba2int(encoded_data[datasize_starting_index:datasize_ending_index])
        data_ending_index = data_starting_index + data_size

        # grab all the encoded data from the huffmanencoding and discard the rest
        huffman_data = encoded_data[data_starting_index:data_ending_index]

        # seperate the header from the encode huffman data
        huffman_stringdata, encoded_data = partition_bitstring(huffman_data, delimiter)

        # seperate the header into the size of the data and the binary representation of huffman tree
        huffman_datasize, huffman_string = (
            ba2int(huffman_stringdata[:_DATA_BINARYSIZE_MARKER_LEN]),
            huffman_stringdata[_DATA_BINARYSIZE_MARKER_LEN:],
        )

        if encoded_dtype == float:
            decimal, huffman_string = ba2int(huffman_string[:_DECIMAL_MARKER_LEN]), huffman_string[_DECIMAL_MARKER_LEN:]
            return decode(huffman_string, encoded_data.to01(), huffman_datasize, encoded_dtype, decimal=decimal)

        return decode(huffman_string, encoded_data.to01(), huffman_datasize, encoded_dtype)

    except Exception:
        raise DecompressionError("Could not read the given file, make sure it has been encoded with the module")


def _build_tree_from_dataset(quantised_dataset: List[Tuple[ValidDataType, int]]) -> Huffman_Node:
    while len(quantised_dataset) != 1:
        (data1, freq_1), (data2, freq_2) = quantised_dataset[:-3:-1]

        quantised_dataset = quantised_dataset[:-2]

        insort(
            quantised_dataset,
            (Huffman_Node(data1, data2), freq_1 + freq_2),
            key=lambda data: -data[1],
        )
    return quantised_dataset[0][0]


def _build_tree_from_bitarray(huffmanString: bitarray, data_size: int, bindecoder: Callable) -> Huffman_Node:
    def traversal_builder(to_process: bitarray):
        next_bit = to_process.pop(0)
        if next_bit == 0:
            bindata = to_process[:data_size].to01()
            return bindecoder(data=bindata), to_process[data_size:]

        left_child, to_process = traversal_builder(to_process)
        right_child, to_process = traversal_builder(to_process)
        return Huffman_Node(left=left_child, right=right_child), to_process

    return traversal_builder(huffmanString)[0]


def _generate_catalogue(huffnode: Huffman_Node, tag: BinaryCode = "") -> Dict[BinaryCode, ValidDataType]:
    if not isinstance(huffnode, Huffman_Node):
        return {tag: huffnode}

    catalogue = {}
    catalogue.update(_generate_catalogue(huffnode.left, tag + "0"))
    catalogue.update(_generate_catalogue(huffnode.right, tag + "1"))

    return catalogue


def partition_bitstring(bitstring: bitarray, sep: BinaryCode) -> Tuple[bitarray, bitarray]:
    sep_index = bitstring.index(bitarray(sep))
    return bitstring[:sep_index], bitstring[sep_index + len(sep) :]


with open("file", "wb") as f:
    dump(
        "popeewnoernfpo",
        f,
    )

with open("file", "rb") as f:
    print(load(f))
