from typing import BinaryIO, Callable, Dict, List, Tuple
from collections import Counter, namedtuple
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
    BinaryCode,
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


Huffman_Node = namedtuple("Huffman_Node", ["left", "right"])


def encode(dataset: ValidDataset) -> Tuple[str, str]:
    """
    encode a given data with Huffman Coding

    Args:
        dataset (Union[str, list, tuple]): data of the type string, a list of int / float

        dtype (ValidDataType): specifying the data type that the datset

        decimal (int, optional): will be used for the float to binary conversion if the datatype given is float. Defaults to 2.

    Raises:
        ValueError: if the decimal place given exceeds the maximum decimal place allowed (10)
        TypeError: if the dataset given does not have homogenous datatype

    Returns:
        Tuple[str, str]: - a binary string representing the huffman tree(for decoding purpose)
                         - a binary string representing the actual encoded data

    * format: datatype_marker + data_size + optional[decimal_marker] + huffman_string
    """

    # type-checking
    if isinstance(dataset, str):
        dtype = str

    elif all(isinstance(data, int) for data in dataset):
        dtype = int

    else:
        try:
            dataset = [float(data) for data in dataset]

        except TypeError as e:
            raise TypeError("inconsistent data type in dataset").with_traceback(e.__traceback__)
        else:
            dtype = float

            # check and get the max decimal place in the data
            decimal = max([len(data) - data.index(".") - 1 for data in [str(d) for d in dataset]])
            if decimal > _MAX_DECIMAL:
                raise ValueError(f"maximum decimal place of '{_MAX_DECIMAL}' exceeded")

    # encoding the data
    huffman_tree = build_tree_from_dataset(Counter(dataset).most_common())
    catalogue = {v: k for k, v in generate_catalogue(huffman_tree).items()}
    encoded_data = encode_dataset(dataset, catalogue)

    # generating the header for the huffman encoding
    binencoder_config = {
        str: {},
        int: {"signed": True},
        float: {"decimal": decimal, "signed": True},
    }
    binencoder = partial(tobin, **binencoder_config[dtype])
    header = _SUPPORTED_DTYPE_TO_BIN[dtype] + generate_huffmanstring(huffman_tree, dtype, binencoder)

    # adding the decimal place indicator
    if dtype == float:
        decimal_marker = format(decimal, f"0{_DECIMAL_MARKER_SIZE}b")
        decimal_marker_index = _DTYPE_MARKER_SIZE + _ELEM_MARKER_SIZE
        header = header[:decimal_marker_index] + decimal_marker + header[decimal_marker_index:]

    return header, encoded_data


def encode_dataset(dataset: ValidDataset, catalogue: Dict[BinaryCode, ValidDataType]) -> BinaryCode:
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


def generate_huffmanstring(
    huffman_tree: Huffman_Node, dtype: ValidDataType, binencoder: Callable[[ValidDataType], BinaryCode]
) -> BinaryCode:
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

    def traverse_huffmantree(huffman_tree: Huffman_Node, max_bitsize: int = 0) -> List[str]:
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
            return ["0", bindata], bindatalen if bindatalen > max_bitsize else max_bitsize

        huffmanString = ["1"]
        for node in [huffman_tree.left, huffman_tree.right]:
            binary_code, max_bitsize = traverse_huffmantree(node, max_bitsize)
            huffmanString.extend(binary_code)

        return huffmanString, max_bitsize

    huffman_list, max_bitsize = traverse_huffmantree(huffman_tree)
    if dtype != str:
        # to preserve the sign of an integer/float
        for index, data in enumerate(huffman_list):
            if huffman_list[index - 1] == "0":
                huffman_list[index] = data[0] + data[1:].zfill(max_bitsize - 1)
    else:
        for index, data in enumerate(huffman_list):
            if huffman_list[index - 1] == "0":
                huffman_list[index] = data.zfill(max_bitsize)

    huffman_list.insert(0, format(max_bitsize, f"0{_ELEM_MARKER_SIZE}b"))

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

    return decode(**data_to_decode)


def build_tree_from_dataset(quantised_dataset: List[Tuple[ValidDataType, int]]) -> Huffman_Node:
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


def build_tree_from_huffmanstring(
    huffmanString: str, data_size: int, bindecoder: Callable[[BinaryCode], ValidDataType]
) -> Huffman_Node:
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

    try:
        return traversal_builder(huffmanString)[0]
    except Exception as err:
        raise CorruptedHeaderError(f"huffmanstring used is unusable, error occured -> {err}")


def generate_catalogue(huffnode: Huffman_Node, tag: BinaryCode = "") -> Dict[BinaryCode, ValidDataType]:
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
    catalogue.update(generate_catalogue(huffnode.left, tag + "0"))
    catalogue.update(generate_catalogue(huffnode.right, tag + "1"))

    return catalogue
