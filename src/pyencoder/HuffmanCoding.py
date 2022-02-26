from typing import Dict, Union, List, Tuple, Deque, BinaryIO
from collections import Counter, deque
from dataclasses import dataclass
from bisect import insort

from bitarray import bitarray

from pyencoder._type_hints import (
    ValidDataType,
    BitCode,
    SUPPORTED_DTYPE,
    DIV,
    _check_datatype,
    _get_dtype_byte_header,
    DecompressionError,
)


@dataclass(frozen=True, slots=True)
class Huffman_Node:

    left: Union["Huffman_Node", str]
    right: Union["Huffman_Node", str]


def encode(dataset: Union[str, list, tuple]) -> Tuple[str, BitCode]:
    # encoding the data
    huffman_tree = _build_tree_from_dataset(Counter(dataset).most_common())
    catalogue = {v: k for k, v in _generate_catalogue(huffman_tree).items()}
    encoded_data = _encode_dataset(dataset, catalogue)

    # generating the string repr of the huffman tree
    huffman_string = _generate_huffmanstring(huffman_tree)

    return huffman_string, encoded_data


def _encode_dataset(dataset: ValidDataType, catalogue: Dict[BitCode, ValidDataType]) -> BitCode:
    if isinstance(dataset, str):
        dataset = list(dataset)
    return "".join([catalogue[data] for data in dataset])


def _generate_huffmanstring(huffman_tree: Huffman_Node, dataset: list) -> List[str]:
    def traverse_huffmantree(huffman_tree: Huffman_Node):
        if not isinstance(huffman_tree, Huffman_Node):
            return [0, huffman_tree]

        huffmanString = [1]
        for node in [huffman_tree.left, huffman_tree.right]:
            huffmanString.extend(traverse_huffmantree(node))

        return huffmanString

    huffman_list = traverse_huffmantree(huffman_tree)


def decode(huffman_string: str, encoded_data: BitCode, dtype: ValidDataType) -> ValidDataType:
    try:
        huffman_tree = _build_tree_from_bitcode(huffman_string, dtype)
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
    dataset: Union[str, list, tuple],
    dtype: ValidDataType,
    file: BinaryIO,
    *,
    delimiter: str = "",
    marker: str = "",
) -> None:
    if delimiter == marker:
        raise ValueError("delimiter and huff marker should not be the same")

    if delimiter:
        delimiter = "".join(f"{ord(i):04b}" for i in delimiter)
        if len(delimiter) > 4:
            raise ValueError("Invalid delimiter: size of delimiter is too big, max=4")
    else:
        delimiter = "DEFAULT_DELIMITER"

    if marker:
        marker = "".join(f"{ord(i):04b}" for i in marker)
        if len(marker) > 16:
            raise ValueError("Invalid marker: size of marker is too big, max=16")
    else:
        marker = "DEFAULT_MARKER"

    header, encoded_data = encode(dataset)

    # the actual data
    huffman_data = header + delimiter + encoded_data

    # the length of the data
    huffman_length = format(len(huffman_data), "32b")

    datapack = bitarray(marker + huffman_length + huffman_data)
    datapack.tofile(file)


def load(file: BinaryIO) -> ValidDataType:
    try:
        dtype, huffman_string, encoded_data = file.read().split(DIV)
    except:
        raise DecompressionError("Could not read the given file, make sure it has been encoded with the module")

    return decode(huffman_string, encoded_data, SUPPORTED_DTYPE[dtype])


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


def _build_tree_from_bitcode(huffmanString: BitCode, bitsize: int, dtype: ValidDataType) -> Huffman_Node:
    to_process = bitarray()
    to_process.frombytes(huffmanString)

    def traversal_builder(next_bit: str, to_process: bitarray):
        if next_bit != 1:

            data_size = int(to_process[:bitsize].to01(), 2)

            data = to_process[bitsize:data_size].tobytes().decode("utf-8")

            to_process = to_process[bitsize + data_size :]

            return dtype(data)

        left_child = traversal_builder(to_process.pop(0), to_process)
        right_child = traversal_builder(to_process.pop(0), to_process)
        return Huffman_Node(left=left_child, right=right_child)

    return traversal_builder(to_process.pop(0), to_process)


def _generate_catalogue(huffnode: Huffman_Node, tag: BitCode = "") -> Dict[BitCode, ValidDataType]:
    if not isinstance(huffnode, Huffman_Node):
        return {tag: huffnode}

    catalogue = {}
    catalogue.update(_generate_catalogue(huffnode.left, tag + "0"))
    catalogue.update(_generate_catalogue(huffnode.right, tag + "1"))

    return catalogue


# with open("file.txt", "wb") as f:
#     dump([1, 2, 3, 4, 4, 4, 4, 4, 4], int, f, delimiter="\0", marker="h")
print(encode([1, 2, 3, 4, 4, 4, 4, 4, 4]))
