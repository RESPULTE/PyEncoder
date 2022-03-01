from bisect import insort
from functools import partial
from collections import Counter, namedtuple
from typing import BinaryIO, Callable, Dict, List, Tuple, Union

from bitarray import bitarray
from bitarray.util import ba2int

from pyencoder._type_hints import CompressionError, DecompressionError, BinaryCode, ValidDataType, ValidDataset
from pyencoder.config import (
    _DTYPEMARKER_LEN,
    _DATASIZEMARKER_LEN,
    _DATA_BINARYSIZE_MARKER_LEN,
    _SUPPORTED_DTYPE_FROM_BIN,
    _SUPPORTED_DTYPE_TO_BIN,
    DELIMITER,
    HUFFMARKER,
    _DECIMAL_MARKER_LEN,
    MAX_DECIMAL,
)
from pyencoder.utils import frombin, tobin


Huffman_Node = namedtuple("Huffman_Node", ["left", "right"])


def encode(dataset: ValidDataset, *, decimal: int = 2) -> Tuple[str, str]:
    """
    encode a given data with Huffman Coding

    Args:
        dataset (Union[str, list, tuple]): data of the type string, a list of int / float

        dtype (ValidDataType): specifying the data type that the datset

        decimal (int, optional): will be used for the float to binary conversion if the datatype given is float.
                                 Defaults to 2.

    Raises:
        ValueError: if the decimal place given exceeds the maximum decimal place allowed (10)
        TypeError: if the dataset given does not have homogenous datatype

    Returns:
        Tuple[str, str]: - a binary string representing the huffman tree(for decoding purpose)
                            * format: datatype_marker + binarydata_size + optional[decimal_marker] + huffman_string
                         - a binary string representing the actual encoded data
    """
    if isinstance(dataset, str):
        dtype = str
    elif all(isinstance(data, int) for data in dataset):
        dtype = int
    else:
        try:
            dataset = [float(data) for data in dataset]
        except TypeError:
            raise CompressionError("inconsistent data type in dataset")
        else:
            dtype = float

    if decimal > MAX_DECIMAL:
        raise ValueError(f"maximum decimal place exceeded: {MAX_DECIMAL}")

    # encoding the data
    huffman_tree = _build_tree_from_dataset(Counter(dataset).most_common())
    catalogue = {v: k for k, v in _generate_catalogue(huffman_tree).items()}
    encoded_data = _encode_dataset(dataset, catalogue)

    # generating the string repr of the huffman tree
    binencoder_config = {
        str: {},
        int: {"signed": True},
        float: {"decimal": decimal, "signed": True},
    }
    dtype_marker = _SUPPORTED_DTYPE_TO_BIN[dtype]
    binencoder = partial(tobin, **binencoder_config[dtype])
    header = dtype_marker + _generate_huffmanstring(huffman_tree, dtype, binencoder)

    if dtype == float:
        decimal_marker = format(decimal, f"0{_DECIMAL_MARKER_LEN}b")
        decimal_marker_index = _DTYPEMARKER_LEN + _DATA_BINARYSIZE_MARKER_LEN
        header = header[:decimal_marker_index] + decimal_marker + header[decimal_marker_index:]

    return header, encoded_data


def _encode_dataset(dataset: ValidDataset, catalogue: Dict[BinaryCode, ValidDataType]) -> BinaryCode:
    """
    [INTERNAL]
    encode the dataset with the given huffman codes

    Args:
        dataset (Union[str, List[int], List[float]]): dataset to encode

        catalogue (Dict[BinaryCode, ValidDataset]):
        a dictionary containing the binary code representing the data as th ekey and the data itself as the value

    Returns:
        BinaryCode: a string of 1 and 0
    """
    if isinstance(dataset, str):
        dataset = list(dataset)
    return "".join([catalogue[data] for data in dataset])


def _generate_huffmanstring(huffman_tree: Huffman_Node, dtype: ValidDataType, binencoder: Callable) -> BinaryCode:
    """
    [INTERNAL]
    generate a binary representation of the huffmann tree

    Args:
        huffman_tree (Huffman_Node): huffman node that is built/complete with data

        binencoder (Callable): an encoder, complete with all the keyword specification (sign/decimal),
                               to encode the data into binary string
                               [using partial from functools to achieve this]

    Returns:
        BinaryCode:  a string of 1 and 0
    """

    def traverse_huffmantree(huffman_tree: Huffman_Node, max_bitsize: List[int]) -> List[str]:
        """
        a recursive internal, internal function to recursively turn the huffman tree into a list of binary string
        and grab the maximum binary string's length of the encoded data
            - "0" marks the beginning of the actual encoded data
            - "1" marks the internal node

        Args:
            huffman_tree (Huffman_Node): huffman node that is built/complete with data


            max_bitsize (List[int]):- used for the sole purpose of getting the maximum binary string's length
                                       to pad the encoded data afterwards and ensure consistent data length
                                    * contains a single integer in the list
                                    * make use of the mutable nature of the python's list to recursively alter the data


        Returns:
            List[str]: a list of 0s and 1s representing the huffman tree
        """
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

    if dtype != str:
        # to preserve the sign of an integer/float
        for index, data in enumerate(huffman_list):
            if huffman_list[index - 1] == "0":
                huffman_list[index] = data[0] + data[1:].zfill(max_bitsize - 1)
    else:
        for index, data in enumerate(huffman_list):
            if huffman_list[index - 1] == "0":
                huffman_list[index] = data.zfill(max_bitsize)

    huffman_list.insert(0, format(max_bitsize, f"0{_DATA_BINARYSIZE_MARKER_LEN}b"))

    return "".join(huffman_list)


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


def dump(dataset: ValidDataset, file: BinaryIO, *, decimal: int = 2, delimiter: int = None, marker: int = None) -> None:
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
    delimiter = tobin(delimiter if delimiter else DELIMITER)
    marker = tobin(marker if marker else HUFFMARKER)

    header, encoded_data = encode(dataset, decimal=decimal)

    # the actual data
    huffman_data = header + delimiter + encoded_data

    # the size of the entire huffmancoding
    huffmancoding_size = format(len(huffman_data), f"0{_DATASIZEMARKER_LEN}b")

    datapack = bitarray(marker + huffmancoding_size + huffman_data)

    datapack.tofile(file)


def load(file: BinaryIO, *, delimiter: str = None, marker: str = None) -> ValidDataset:
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
    marker = tobin(marker if marker else HUFFMARKER)
    delimiter = tobin(delimiter if delimiter else DELIMITER)

    encoded_huffdata = bitarray()
    encoded_huffdata.frombytes(file.read())

    _, encoded_huffdata = __partition_bitarray(encoded_huffdata, marker)

    huffmancoding_size = ba2int(encoded_huffdata[:_DATASIZEMARKER_LEN])

    huffman_data = encoded_huffdata[_DATASIZEMARKER_LEN : _DATASIZEMARKER_LEN + huffmancoding_size]

    header, encoded_data = __partition_bitarray(huffman_data, delimiter)

    dtype, huffman_string = _SUPPORTED_DTYPE_FROM_BIN[header[:_DTYPEMARKER_LEN].to01()], header[_DTYPEMARKER_LEN:]

    # seperate the header into the size of the data and the binary representation of huffman tree

    max_datasize, huffman_string = (
        ba2int(huffman_string[:_DATA_BINARYSIZE_MARKER_LEN]),
        huffman_string[_DATA_BINARYSIZE_MARKER_LEN:],
    )
    if dtype == float:
        decimal, huffman_string = ba2int(huffman_string[:_DECIMAL_MARKER_LEN]), huffman_string[_DECIMAL_MARKER_LEN:]
        return decode(huffman_string.to01(), encoded_data.to01(), max_datasize, dtype, decimal=decimal)

    return decode(huffman_string.to01(), encoded_data.to01(), max_datasize, dtype)


def _build_tree_from_dataset(quantised_dataset: List[Tuple[ValidDataType, int]]) -> Huffman_Node:
    """
    [INTERNAL]
    create a huffman tree from a counted dataset, i.e frequency of each data s counted

    Args:
        quantised_dataset (List[Tuple[ValidDataType, int]]): a counted dataset, i.e frequency of each data counted

    Returns:
        Huffman_Node: a huffman tree
    """
    while len(quantised_dataset) != 1:
        (data1, freq_1), (data2, freq_2) = quantised_dataset[:-3:-1]

        quantised_dataset = quantised_dataset[:-2]

        insort(
            quantised_dataset,
            (Huffman_Node(data1, data2), freq_1 + freq_2),
            key=lambda data: -data[1],
        )
    return quantised_dataset[0][0]


def _build_tree_from_bitarray(huffmanString: str, data_size: int, bindecoder: Callable) -> Huffman_Node:
    """
    [INTERNAL]
    rebuild the huffman tree from a bitarray

    Args:
        huffmanString (str): a string of 0 and 1

        data_size (int): the size of each encoded data, should be the same for all

        bindecoder (Callable): an decoder, complete with all the keyword specification (sign/decimal),
                               to decode the data from binary string
                               [using partial from functools to achieve this]

    Returns:
        Huffman_Node: a huffman tree
    """

    def traversal_builder(to_process: str) -> Tuple[Huffman_Node, str]:
        next_bit, to_process = to_process[0], to_process[1:]

        if next_bit == "0":
            bindata = to_process[:data_size]
            return bindecoder(data=bindata), to_process[data_size:]

        left_child, to_process = traversal_builder(to_process)
        right_child, to_process = traversal_builder(to_process)
        return Huffman_Node(left=left_child, right=right_child), to_process

    return traversal_builder(huffmanString)[0]


def _generate_catalogue(huffnode: Huffman_Node, tag: BinaryCode = "") -> Dict[BinaryCode, ValidDataType]:
    """
    [INTERNAL]
    generate a dictionary for encoding purposes
    - key: huffman_code
    - value: actual data

    Args:
        huffnode (Huffman_Node): a huffman tree class
        tag (BinaryCode, optional): a parameter used solely for recursion, no value should be given. Defaults to "".

    Returns:
        Dict[BinaryCode, ValidDataType]: a catalogue for encoding purposes
    """
    if not isinstance(huffnode, Huffman_Node):
        return {tag: huffnode}

    catalogue = {}
    catalogue.update(_generate_catalogue(huffnode.left, tag + "0"))
    catalogue.update(_generate_catalogue(huffnode.right, tag + "1"))

    return catalogue


def __partition_bitarray(bitstring: bitarray, delimiter: BinaryCode) -> Tuple[bitarray, bitarray]:
    """a helper function to parition the bitarray into two parts with the given delimeter

    Args:
        bitstring (bitarray): an array containning 0 and 1
        delimiter (BinaryCode): string containning 1 and 0

    Returns:
        Tuple[bitarray, bitarray]: two part of the seperated bitarray
    """
    sep_index = bitstring.index(bitarray(delimiter))
    return bitstring[:sep_index], bitstring[sep_index + len(delimiter) :]
