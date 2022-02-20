from typing import Dict, Union, List, Tuple, Deque, BinaryIO
from collections import Counter, deque
from dataclasses import dataclass
from bisect import insort

from pyencoder._type_hints import (
    ValidDataType, 
    BitCode, 
    SUPPORTED_DTYPE, 
    DIV, 
    _check_datatype,
    _get_dtype_header,
    DecompressionError
)


@dataclass(frozen=True, slots=True)
class Huffman_Node:

    left: Union['Huffman_Node', str]
    right: Union['Huffman_Node', str]



def encode(dataset: Union[str, list, tuple], dtype: ValidDataType) -> Tuple[str, BitCode]:
    _check_datatype(dataset, dtype)

    huffman_tree = _build_tree_from_dataset(Counter(dataset).most_common())
    huffman_string = _generate_bitcode(huffman_tree)

    catalogue = _generate_catalogue(huffman_tree)
    encoded_data = _encode(dataset, catalogue)

    return huffman_string, encoded_data


def decode(huffman_string: str, encoded_data: BitCode, dtype: ValidDataType) -> ValidDataType:
    try:
        huffman_tree = _build_tree_from_bitcode(huffman_string, dtype)
        catalogue = _generate_catalogue(huffman_tree)

        current_node = huffman_tree
        decoded_data = []
        curr_tag = ""

        for tag in encoded_data:

            current_node = current_node.left if tag == '0' else current_node.right

            curr_tag += tag
            if not isinstance(current_node, Huffman_Node):
                decoded_data.append(catalogue[curr_tag])
                current_node = huffman_tree
                curr_tag = ''
                continue

    except Exception as e:
        raise DecompressionError(f"Unknown error has occured -> {e}")

    else:
        return "".join(decoded_data) if dtype == str else decoded_data


def dump(dataset: Union[str, list, tuple], file: BinaryIO, dtype: ValidDataType) -> None:
    huffman_string, encoded_data = encode(dataset, dtype)
    
    dtype = _get_dtype_header(dtype)
    header = huffman_string.encode('utf-8')
    datapack = encoded_data.encode('utf-8')

    file.write(dtype + DIV + header + DIV + datapack)


def load(file: BinaryIO) -> None:
    try:
        dtype, raw_header, raw_datapack = file.read().split(DIV)
    except:
        raise DecompressionError(
            "Could not read the given file, make sure it has been encoded with the module"
        )

    encoded_data = raw_datapack.decode('utf-8')
    huffman_string = raw_header.decode('utf-8')

    return decode(huffman_string, encoded_data, SUPPORTED_DTYPE[dtype])


def _build_tree_from_dataset(quantised_dataset: List[Tuple[ValidDataType, int]]) -> Huffman_Node:

    while len(quantised_dataset) != 1:
        (data1, freq_1), (data2, freq_2) = quantised_dataset[:-3:-1]

        quantised_dataset = quantised_dataset[:-2]

        insort(
            quantised_dataset,
            (Huffman_Node(data1, data2), freq_1 + freq_2),
            key=lambda data: -data[1]
        )
    return quantised_dataset[0][0]


def _build_tree_from_bitcode(huffmanString: BitCode, dtype: ValidDataType) -> Huffman_Node:
    to_process: Deque[str] = deque(list(huffmanString))

    def traversal_builder(next_bit: str, to_process: Deque[str]):
        if next_bit == "(":
            if dtype == str:
                return to_process.popleft()

            data = ""
            while to_process[0] != ")":
                data += to_process.popleft()

            # to get rid of ')'
            to_process.popleft()
            return dtype(data)

        left_child = traversal_builder(to_process.popleft(), to_process)
        right_child = traversal_builder(to_process.popleft(), to_process)
        return Huffman_Node(left=left_child, right=right_child)

    return traversal_builder(to_process.popleft(), to_process)


def _generate_bitcode(huffman_tree: Huffman_Node) -> BitCode:
    if not isinstance(huffman_tree, Huffman_Node):
        if isinstance(huffman_tree, str):
            return f"({huffman_tree}"
        return f"({huffman_tree})"

    huffmanString = "1"
    for node in [huffman_tree.left, huffman_tree.right]:
        huff = _generate_bitcode(node)
        huffmanString += huff

    return huffmanString


def _generate_catalogue(huffnode: Huffman_Node, tag: BitCode = "") -> Dict[BitCode, ValidDataType]:
    if not isinstance(huffnode, Huffman_Node):
        return {tag: huffnode}

    catalogue = {}
    catalogue.update(_generate_catalogue(huffnode.left, tag + '0'))
    catalogue.update(_generate_catalogue(huffnode.right, tag + '1'))

    return catalogue


def _encode(dataset: ValidDataType, catalogue: Dict[BitCode, ValidDataType]) -> BitCode:
    if isinstance(dataset, str):
        dataset = list(dataset)
    return "".join([next(k for k, v in catalogue.items() if v == data) for data in dataset])
