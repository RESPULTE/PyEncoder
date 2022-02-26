from typing import Dict, Union, List, Tuple, Deque, BinaryIO
from collections import Counter, deque
from dataclasses import dataclass
from bisect import insort

from bitarray import bitarray
from bitarray.util import ba2int, int2ba

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


def encode(dataset: Union[str, list, tuple], dtype: ValidDataType) -> Tuple[str, BitCode]:
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


def dump(
    dataset: Union[str, list, tuple], dtype: ValidDataType, file: BinaryIO, *, delimiter: str = "", marker: str = ""
) -> None:
    if delimiter == marker:
        raise ValueError("delimiter and huff marker should not be the same")

    if delimiter:
        if isinstance(delimiter, str):
            delimiter = "".join(f"{ord(i):b}" for i in delimiter)
        else:
            delimiter = format(delimiter, "04b")
    else:
        delimiter = "DEFAULT_DELIMITER"

    if marker:
        if isinstance(marker, str):
            marker = "".join(f"{ord(i):b}" for i in marker)
        else:
            marker = format(marker, "04b")

    else:
        marker = "DEFAULT_MARKER"

    header, encoded_data = encode(dataset, dtype)

    # the actual data
    huffman_data = header + delimiter + encoded_data

    # the length of the data
    huffman_length = format(len(huffman_data), "032b")

    datapack = bitarray(marker + huffman_length + huffman_data)
    datapack.tofile(file)


def load(file: BinaryIO, *, delimiter: str = "", marker: str = "") -> ValidDataType:
    if delimiter == marker:
        raise ValueError("delimiter and huff marker should not be the same")

    if delimiter:
        if isinstance(delimiter, str):
            delimiter = delimiter.encode("utf-8")
        else:
            delimiter = int2ba(delimiter)
    else:
        delimiter = "DEFAULT_DELIMITER"

    if marker:
        if isinstance(marker, str):
            marker = marker.encode("utf-8")
        else:
            marker = int2ba(marker)

    else:
        marker = "DEFAULT_MARKER"
    try:
        encoded_data = bitarray()
        encoded_data.frombytes(file.read())
        starting_index = encoded_data.index(marker) + len(marker)
        huffman_size = ba2int(encoded_data[starting_index : starting_index + 32])
        huffman_data = encoded_data[starting_index + 32 : starting_index + huffman_size + 32]

        delimiter_index = huffman_data.index(delimiter)
        huffman_stringdata, encoded_data = (
            huffman_data[:delimiter_index],
            huffman_data[delimiter_index + len(delimiter) :],
        )

        huffman_datasize, huffman_string = ba2int(huffman_stringdata[:32]), huffman_stringdata[32:]

    except:
        raise DecompressionError("Could not read the given file, make sure it has been encoded with the module")
    else:
        return decode(huffman_string, encoded_data, huffman_datasize, int)


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


def _build_tree_from_bitcode(huffmanString: BitCode, data_size: int, dtype: ValidDataType) -> Huffman_Node:
    def traversal_builder(next_bit: str, to_process: bitarray):
        if next_bit == 0:
            return dtype(ba2int(to_process[:data_size])), to_process[data_size:]

        if to_process:
            left_child, to_process = traversal_builder(to_process.pop(0), to_process)
        if to_process:
            right_child, to_process = traversal_builder(to_process.pop(0), to_process)
        return Huffman_Node(left=left_child, right=right_child), to_process

    return traversal_builder(huffmanString.pop(0), huffmanString)[0]


def _generate_catalogue(huffnode: Huffman_Node, tag: BitCode = "") -> Dict[BitCode, ValidDataType]:
    if not isinstance(huffnode, Huffman_Node):
        return {tag: huffnode}

    catalogue = {}
    catalogue.update(_generate_catalogue(huffnode.left, tag + "0"))
    catalogue.update(_generate_catalogue(huffnode.right, tag + "1"))

    return catalogue


with open("file.txt", "wb") as f:
    dump([1, 2, 3, 4, 4, 4, 4, 4, 4], int, f, delimiter=1219, marker=11)

with open("file.txt", "rb") as f:
    print(load(f, delimiter=1219, marker=11))
