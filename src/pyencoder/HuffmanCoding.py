from heapq import heappop, heappush, heapify
from collections import Counter
from typing import BinaryIO, Literal, Optional, Type, Tuple, Dict, List, overload

from pyencoder import config
from pyencoder.utils.binary import frombin, frombytes, tobin, tobytes
from pyencoder.type_hints import (
    CorruptedHeaderError,
    CorruptedEncodingError,
    SupportedDataType,
    ValidDataType,
    ValidDataset,
    Bitcode,
)


@overload
def decode(
    header: Bitcode,
    encoded_data: Bitcode,
    dtype: Literal["b", "B", "h", "H", "i", "I", "l", "L", "q", "Q", "f", "d", "s"],
    length_encoding: bool = False,
) -> ValidDataset:
    ...


@overload
def decode(
    header: Bitcode,
    encoded_data: Bitcode,
    dtype: Type[int] | Type[float] | Type[str],
    length_encoding: bool = False,
) -> ValidDataset:
    ...


def decode(
    codebook: Dict[ValidDataType, Bitcode],
    encoded_data: Bitcode,
    dtype: SupportedDataType,
    length_encoding: bool = False,
) -> ValidDataset:

    decoded_data = [None] * len(encoded_data)
    to_process = encoded_data
    curr_index = 0
    curr_code = ""

    if length_encoding:
        if dtype not in ("s", "f", "d", str, float):
            dtype = int

        while to_process:
            curr_code += to_process[:1]
            to_process = to_process[1:]

            if curr_code not in codebook:
                continue

            curr_elem_binsize = codebook[curr_code]
            curr_elem = frombin(to_process[:curr_elem_binsize], dtype)
            decoded_data[curr_index] = curr_elem

            to_process = to_process[curr_elem_binsize:]
            curr_index += 1
            curr_code = ""
    else:
        while to_process:
            curr_code += to_process[:1]
            to_process = to_process[1:]

            if curr_code not in codebook:
                continue

            decoded_data[curr_index] = codebook[curr_code]
            curr_index += 1
            curr_code = ""

    decoded_data = decoded_data[:curr_index]

    return decoded_data if dtype not in ("s", str) else "".join(decoded_data)


@overload
def encode(
    dataset: List[float | int],
    dtype: Literal["b", "B", "h", "H", "i", "I", "l", "L", "q", "Q", "f", "d", "s"],
    length_encoding: bool = False,
):
    ...


@overload
def encode(dataset: List[float | int], dtype: Type[float] | Type[int] | Type[str], length_encoding: bool = False):
    ...


def encode(
    dataset: ValidDataset, dtype: Optional[SupportedDataType], length_encoding: bool = False
) -> Tuple[Dict[ValidDataType, Bitcode], Bitcode]:
    if not length_encoding:
        codebook = generate_canonical_codebook(dataset)
        encoded_data = "".join([codebook[data] for data in dataset])
        return codebook, encoded_data

    if dtype not in ("s", "f", "d", float, str):
        dtype = int
    bin_dataset = [tobin(data, dtype) for data in dataset]
    binlen_dataset = [len(data) for data in bin_dataset]

    codebook = generate_canonical_codebook(binlen_dataset)
    encoded_data = "".join(
        x for binlen, bindata in zip(binlen_dataset, bin_dataset) for x in (codebook[binlen], bindata)
    )

    return codebook, encoded_data


def dump(
    dataset: ValidDataset,
    dtype: SupportedDataType,
    file: BinaryIO,
    *,
    length_encoding: bool = False,
    sof_marker: Optional[ValidDataType] = None,
    eof_marker: Optional[ValidDataType] = None,
) -> None:
    codebook, encoded_data = encode(dataset, dtype=dtype, length_encoding=length_encoding)

    codelengths, symbols = generate_header_from_codebook(
        codebook, dtype if not length_encoding else config.LENGTH_ENCODING_DATA_DTYPE
    )

    header_size = tobin(len(codelengths + symbols), config.HEADER_MARKER_DTYPE, bitlength=config.HEADER_MARKER_BITSIZE)

    sof_marker = tobin(sof_marker or config.SOF_MARKER, config.MARKER_DTYPE, bitlength=config.MARKER_BITSIZE)
    eof_marker = tobin(eof_marker or config.EOF_MARKER, config.MARKER_DTYPE, bitlength=config.MARKER_BITSIZE)

    bin_data = tobytes(sof_marker + header_size + codelengths + symbols + encoded_data + eof_marker, "bin")
    file.write(bin_data)

    return bin_data


def load(
    file: BinaryIO,
    dtype: SupportedDataType,
    *,
    length_encoding: bool = False,
    sof_marker: Optional[ValidDataType] = None,
    eof_marker: Optional[ValidDataType] = None,
) -> ValidDataset:
    raw_bindata = frombytes(file.read(), "bin")

    sof_marker = tobin(sof_marker or config.SOF_MARKER, config.MARKER_DTYPE, bitlength=config.MARKER_BITSIZE)
    eof_marker = tobin(eof_marker or config.EOF_MARKER, config.MARKER_DTYPE, bitlength=config.MARKER_BITSIZE)

    try:
        raw_encoded_data = raw_bindata.split(sof_marker, maxsplit=1)[1].rsplit(eof_marker, maxsplit=1)[0]
        if raw_encoded_data == "":
            raise CorruptedEncodingError("faulty EOF or SOF marker")

        header_size, huffman_data = (
            frombin(raw_encoded_data[: config.HEADER_MARKER_BITSIZE], config.HEADER_MARKER_DTYPE),
            raw_encoded_data[config.HEADER_MARKER_BITSIZE :],
        )

        header, encoded_data = huffman_data[:header_size], huffman_data[header_size:]

        codebook = generate_codebook_from_header(
            header, dtype if not length_encoding else config.LENGTH_ENCODING_DATA_DTYPE
        )
        return decode(codebook, encoded_data, dtype, length_encoding)

    except Exception as err:
        raise CorruptedEncodingError("encoding cannot be decoded") from err


def generate_header_from_codebook(
    codebook: Dict[ValidDataType, Bitcode], dtype: SupportedDataType
) -> Tuple[Bitcode, Bitcode]:
    codelengths = ["0" * config.CODELENGTH_BITSIZE for _ in range(config.MAX_CODELENGTH)]
    counted_codelengths = Counter([len(code) for code in codebook.values()])

    for length, count in counted_codelengths.items():
        codelengths[length - 1] = tobin(count, config.CODELENGTH_DTYPE, bitlength=config.CODELENGTH_BITSIZE)

    codelengths = "".join(codelengths)
    symbols = tobin("".join(codebook.keys()) if dtype in ("s", str) else codebook.keys(), dtype)

    return codelengths, symbols


def generate_codebook_from_dataset(dataset: ValidDataset = None) -> Dict[ValidDataType, Bitcode]:
    # putting the symbol in a list to allow concatenation for 'int' and 'float' during the 'tree building process'
    counted_dataset = Counter(dataset).most_common()
    counted_dataset = [
        ((0, 2), 37838),
        ((0, 1), 28872),
        ((1, 1), 14430),
        ((2, 1), 8107),
        ((0, 3), 7785),
        ((3, 1), 5213),
        ((0, 4), 4482),
        ((15, 2), 4228),
        ((4, 1), 3581),
        ((1, 2), 3024),
        ((5, 1), 2794),
        ((6, 1), 2456),
        ((0, 5), 2224),
        ((7, 1), 1685),
        ((8, 1), 1407),
        ((9, 1), 1316),
        ((10, 1), 1164),
        ((1, 3), 939),
        ((11, 1), 856),
        ((12, 1), 724),
        ((13, 1), 686),
        ((0, 6), 683),
        ((2, 2), 670),
        ((14, 1), 647),
        ((15, 1), 553),
        ((3, 2), 332),
        ((1, 4), 282),
        ((2, 3), 181),
        ((16, 1), 163),
        ((4, 2), 158),
        ((17, 1), 126),
        ((18, 1), 105),
        ((5, 2), 98),
        ((19, 1), 95),
        ((3, 3), 71),
        ((0, 7), 61),
        ((20, 1), 60),
        ((1, 5), 56),
        ((2, 4), 39),
        ((6, 2), 37),
        ((27, 1), 34),
        ((23, 1), 33),
        ((21, 1), 33),
        ((24, 1), 31),
        ((22, 1), 25),
        ((7, 2), 21),
        ((26, 1), 20),
        ((25, 1), 19),
        ((4, 3), 19),
        ((29, 1), 17),
        ((1, 6), 17),
        ((5, 3), 16),
        ((8, 2), 14),
        ((30, 1), 13),
        ((32, 1), 12),
        ((28, 1), 10),
        ((3, 4), 9),
        ((2, 5), 7),
        ((5, 4), 6),
        ((31, 1), 5),
        ((4, 4), 5),
        ((9, 2), 5),
        ((3, 5), 3),
        ((7, 3), 3),
        ((34, 1), 2),
        ((6, 3), 2),
        ((2, 6), 2),
        ((9, 3), 2),
        ((10, 2), 2),
        ((41, 1), 1),
        ((40, 1), 1),
        ((2, 7), 1),
        ((6, 4), 1),
        ((4, 5), 1),
        ((1, 7), 1),
    ]
    # [(frequency, max_bitlength, symbol)]
    to_process = [(count, 1, [symbol]) for symbol, count in counted_dataset]
    codebook = {symbol: 0 for symbol, _ in counted_dataset}

    heapify(to_process)
    # building the huffman tree
    while len(to_process) != 1:
        tree_freq_1, tree_max_bitlength_1, tree_1 = heappop(to_process)
        tree_freq_2, tree_max_bitlength_2, tree_2 = heappop(to_process)

        new_subtree = tree_1 + tree_2
        new_subtree_freq = tree_freq_1 + tree_freq_2
        new_subtree_max_bitlength = max(tree_max_bitlength_1, tree_max_bitlength_2) + 1

        for sym in new_subtree:
            codebook[sym] += 1

        balance_factor = 0
        if to_process:
            balance_factor = to_process[0][0]

        heappush(
            to_process,
            (
                new_subtree_freq + balance_factor,
                new_subtree_max_bitlength,
                new_subtree,
            ),
        )

    else:
        if len(codebook) == 1:
            return {k: v + 1 for k, v in codebook.items()}

    return codebook


def generate_canonical_codebook(dataset: ValidDataset) -> Dict[ValidDataType, Bitcode]:
    codebook = generate_codebook_from_dataset(dataset)

    # just to ensure that the very first value will be zero
    curr_code = -1
    # making sure that the bit shift won't ever happen for the first value
    prev_bitlength = float("inf")
    # sort the codebook by the bitlength
    to_process = sorted([(bitlength, symbol) for symbol, bitlength in codebook.items()])

    canonical_codebook = {}
    for bitlength, symbol in to_process:

        # increment the code, which is in integer form btw, by 1
        # if the bitlength of this symbol is more than the last symbol, left-shift the code using bitwise operation
        curr_code += 1
        if bitlength > prev_bitlength:
            curr_code = curr_code << (bitlength - prev_bitlength)

        canonical_codebook[symbol] = tobin(curr_code, "I", bitlength=bitlength)
        prev_bitlength = bitlength

    return canonical_codebook


def generate_codebook_from_header(header: Bitcode, dtype: SupportedDataType) -> Dict[Bitcode, ValidDataType]:
    try:
        codelength_info = config.CODELENGTH_BITSIZE * config.MAX_CODELENGTH
        bin_codelengths, bin_symbols = header[:codelength_info], header[codelength_info:]

        num_symbols_per_codelength = [
            int(bin_codelengths[bitlen : bitlen + config.CODELENGTH_BITSIZE], 2)
            for bitlen in range(0, len(bin_codelengths), config.CODELENGTH_BITSIZE)
        ]

        num_codelength = len(num_symbols_per_codelength)
        if num_codelength != config.MAX_CODELENGTH:
            raise ValueError(
                f"number of symbols decoded({num_codelength}) does not match the default values({config.MAX_CODELENGTH})"
            )
        symbols = frombin(bin_symbols, dtype, num=sum(num_symbols_per_codelength))
        if not isinstance(symbols, list):
            symbols = [symbols]
    except (IndexError, ValueError) as err:
        raise CorruptedHeaderError("Header cannot be decoded") from err

    codebook = {}
    curr_code = 0
    curr_sym_index = 0

    for bitlength, num in enumerate(num_symbols_per_codelength, start=1):

        for _ in range(num):
            bincode = tobin(curr_code, config.CODELENGTH_DTYPE, bitlength=bitlength)
            codebook[bincode] = symbols[curr_sym_index]
            curr_sym_index += 1
            curr_code += 1

        curr_code = curr_code << 1

    return codebook
