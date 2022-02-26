from typing import Dict, Union, List, Tuple, Deque, BinaryIO
from collections import Counter, deque
from dataclasses import dataclass
from bisect import insort

from bitarray import bitarray
from bitarray.util import ba2int, int2ba

from pyencoder._type_hints import (
    ValidDataType,
    BitCode,
    DecompressionError,
)

DEFAULT_DELIMITER = 69420
DEFAULT_MARKER = 42069


@dataclass(frozen=True, slots=True)
class Huffman_Node:

    left: Union["Huffman_Node", str]
    right: Union["Huffman_Node", str]


def encode(dataset: Union[str, list, tuple], dtype: ValidDataType) -> Tuple[str, str]:
    # encoding the data
    huffman_tree = _build_tree_from_dataset(Counter(dataset).most_common())
    catalogue = {v: k for k, v in _generate_catalogue(huffman_tree).items()}
    encoded_data = _encode_dataset(dataset, catalogue)

    # generating the string repr of the huffman tree
    huffman_string = _generate_huffmanstring(huffman_tree, dtype)

    return huffman_string, encoded_data


def _encode_dataset(dataset: ValidDataType, catalogue: Dict[BitCode, ValidDataType]) -> BitCode:
    if isinstance(dataset, str):
        dataset = list(dataset)
    return "".join([catalogue[data] for data in dataset])


def _generate_huffmanstring(huffman_tree: Huffman_Node, dtype: ValidDataType) -> List[str]:
    unique_datalist = []

    def traverse_huffmantree(huffman_tree: Huffman_Node):
        if not isinstance(huffman_tree, Huffman_Node):
            unique_datalist.append(huffman_tree)
            return ["0", huffman_tree]

        huffmanString = ["1"]
        for node in [huffman_tree.left, huffman_tree.right]:
            huffmanString.extend(traverse_huffmantree(node))

        return huffmanString

    huffman_list = traverse_huffmantree(huffman_tree)

    bindata_and_binSize: Dict[str, str] = {}
    max_bitsize = 0
    for data in unique_datalist:

        binData = format(ord(data) if dtype == str else data, "b")
        bindata_and_binSize[data] = binData
        binSize = len(binData)

        if binSize > max_bitsize:
            max_bitsize = binSize

    for index, data in enumerate(huffman_list):
        if huffman_list[index - 1] == "0":
            huffman_list[index] = bindata_and_binSize[data].zfill(max_bitsize)

    huffman_list.insert(0, format(max_bitsize, f"0{32}b"))

    return "".join(huffman_list)


def decode(huffman_string: str, encoded_data: bitarray, data_size: int, dtype: ValidDataType) -> ValidDataType:
    try:
        huffman_tree = _build_tree_from_bitcode(huffman_string, data_size, dtype)
        catalogue = _generate_catalogue(huffman_tree)

        current_node = huffman_tree
        decoded_data = []
        curr_tag = ""

        for tag in encoded_data.to01():

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


def dump(dataset: Union[str, list, tuple], file: BinaryIO, *, delimiter: int = None, marker: int = None) -> None:
    if delimiter == marker:
        raise ValueError("delimiter and huff marker should not be the same")

    dtype = str if not isinstance(dataset, list) else int
    if dtype == int:
        if not all(isinstance(data, int) for data in dataset):
            raise ValueError("dataset must be a list of 'int' or a 'str'")

    delimiter = format(delimiter if delimiter else DEFAULT_DELIMITER, "b")
    marker = format(marker if marker else DEFAULT_MARKER, "b")

    header, encoded_data = encode(dataset, dtype)

    # the actual data
    huffman_data = header + delimiter + encoded_data

    dtype = "0" if dtype == str else "1"

    # the size of the data
    huffman_size = format(len(huffman_data), "032b")

    datapack = bitarray(marker + dtype + huffman_size + huffman_data)
    datapack.tofile(file)


def load(file: BinaryIO, *, delimiter: int = "", marker: int = "") -> ValidDataType:
    if delimiter == marker:
        raise ValueError("delimiter and huff marker should not be the same")

    delimiter = int2ba(delimiter if delimiter else DEFAULT_DELIMITER)
    marker = int2ba(marker if marker else DEFAULT_MARKER)

    try:
        encoded_data = bitarray()
        encoded_data.frombytes(file.read())

        huff_block_index = encoded_data.index(marker) + len(marker)
        encoded_dtype = str if encoded_data[huff_block_index] == 0 else int

        starting_index = huff_block_index + 1
        huffman_size = ba2int(encoded_data[starting_index : starting_index + 32])
        huffman_data = encoded_data[starting_index + 32 : starting_index + 32 + huffman_size]

        huffman_stringdata, encoded_data = __partition_bitstring(huffman_data, delimiter)
        huffman_datasize, huffman_string = ba2int(huffman_stringdata[:32]), huffman_stringdata[32:]

    except:
        raise DecompressionError("Could not read the given file, make sure it has been encoded with the module")
    else:
        return decode(huffman_string, encoded_data, huffman_datasize, encoded_dtype)


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


def _build_tree_from_bitcode(huffmanString: bitarray, data_size: int, dtype: ValidDataType) -> Huffman_Node:
    def traversal_builder(to_process: bitarray):
        next_bit = to_process.pop(0)
        if next_bit == 0:
            data = ba2int(to_process[:data_size])
            if dtype == str:
                data = chr(data)
            return data, to_process[data_size:]

        left_child, to_process = traversal_builder(to_process)
        right_child, to_process = traversal_builder(to_process)
        return Huffman_Node(left=left_child, right=right_child), to_process

    return traversal_builder(huffmanString)[0]


def _generate_catalogue(huffnode: Huffman_Node, tag: BitCode = "") -> Dict[BitCode, ValidDataType]:
    if not isinstance(huffnode, Huffman_Node):
        return {tag: huffnode}

    catalogue = {}
    catalogue.update(_generate_catalogue(huffnode.left, tag + "0"))
    catalogue.update(_generate_catalogue(huffnode.right, tag + "1"))

    return catalogue


def __partition_bitstring(bitstring: bitarray, sep: bitarray) -> Tuple[bitarray, bitarray]:
    sep_index = bitstring.index(sep)
    return bitstring[:sep_index], bitstring[sep_index + len(sep) :]


with open("file", "wb") as f:
    dump([1, 2, "a3"], f, delimiter=20202, marker=16901)

with open("file", "rb") as f:
    print(load(f, delimiter=20202, marker=16901))
