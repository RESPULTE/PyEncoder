import math
import operator
import bisect
import dataclasses
from heapq import heappop, heappush, heapify
from collections import Counter, OrderedDict

from typing import Any, Generator, Iterable, Tuple, Dict, List

from pyencoder.HuffmanCoding import config
import pyencoder.config as main_config
from pyencoder.utils.binary import frombin, frombytes, tobin, tobytes
from pyencoder.type_hints import (
    CorruptedHeaderError,
    CorruptedEncodingError,
    SupportedDataType,
    ValidData,
    ValidDataset,
    Bitcode,
)

FIXED_CODE_SIZE = math.ceil(math.log2(main_config.NUM_SYMBOLS))
FIXED_CODE_LOOKUP = {k: "{num:0{size}b}".format(num=i, size=FIXED_CODE_SIZE) for i, k in enumerate(main_config.SYMBOLS)}
FIXED_SYMBOL_LOOKUP = {v: k for k, v in FIXED_CODE_LOOKUP.items()}


@dataclasses.dataclass
class HuffmanNode:
    symbol: ValidData
    weight: int
    order: int = dataclasses.field(compare=True)

    parent: "HuffmanNode" = dataclasses.field(default=None, repr=False)
    left: "HuffmanNode" = dataclasses.field(default=None, repr=False)
    right: "HuffmanNode" = dataclasses.field(default=None, repr=False)

    @property
    def is_branch(self) -> bool:
        return self.parent is not None and self.symbol is None and self.weight > 0

    @property
    def is_leaf(self) -> bool:
        return self.symbol is not None and self.weight > 0

    @property
    def is_root(self) -> bool:
        return self.parent is None and self.symbol is None and self.weight > 0

    def __gt__(self, other: "HuffmanNode") -> bool:
        if self.order > other.order:
            if self.is_leaf and other.is_branch:
                return False
            return True
        if self.is_branch and other.is_leaf:
            return False
        return True

    def __lt__(self, other: "HuffmanNode") -> bool:
        if self.order < other.order:
            if self.is_branch and other.is_leaf:
                return False
            return True
        if self.is_leaf and other.is_branch:
            return True
        return False


class AdaptiveHuffmanTree:
    def __init__(self) -> None:
        self.symbol_catalogue: Dict[str, HuffmanNode] = {}
        self.weight_catalogue: OrderedDict[int, List[HuffmanNode]] = OrderedDict({1: []})
        self.order_index = 2 * main_config.NUM_SYMBOLS - 1

        self.root = self.NYT = HuffmanNode(None, 0, self.order_index)

    def increment_node_weight(self, node: HuffmanNode) -> None:
        # every time a node is promoted, the node is sorted into the list
        # thus, the list maintains sorted by 'order' at all times
        self.weight_catalogue[node.weight].remove(node)
        node.weight += 1
        weight_category = self.weight_catalogue.setdefault(node.weight, [])
        bisect.insort(weight_category, node, key=operator.attrgetter("order"))

    def pre_process(self, node: HuffmanNode) -> HuffmanNode:
        arr = self.weight_catalogue[node.weight]

        # * Note: the list is sorted by 'order' at all times
        # by definition the order of a child must be smaller than its parent
        # so if the node with the highest order is the node's parent
        # the next node with the highest order must be the node and thus no relocation is needed
        highest_order_node = arr[-1]
        node_original_parent = node.parent
        if highest_order_node not in (node, node.parent):
            self.relocate_node(node, highest_order_node)

            if node.weight == highest_order_node.weight:
                ind_1 = arr.index(node)
                ind_2 = arr.index(highest_order_node)
                arr[ind_1], arr[ind_2] = arr[ind_2], arr[ind_1]

        self.increment_node_weight(node_original_parent)

        return node.parent

    def update(self, node: HuffmanNode) -> None:
        while not node.is_root:

            arr = self.weight_catalogue[node.weight]

            # * Note: the list is sorted by 'order' at all times
            # by definition the order of a child must be smaller than its parent
            # so if the node with the highest order is the node's parent
            # the next node with the highest order must be the node and thus no relocation is needed
            highest_order_node = arr[-1]
            if highest_order_node not in (node, node.parent):
                self.relocate_node(node, highest_order_node)

            self.increment_node_weight(node)
            node = node.parent

    def create_node(self, symbol: str) -> HuffmanNode:
        # setting the NYT node as the parent and spawning two new children for it
        parent = self.NYT
        weight = 1

        leaf = HuffmanNode(symbol, weight, self.order_index - 1, parent)
        self.NYT = HuffmanNode(None, 0, self.order_index - 2, parent)

        # updating parent's attributes
        parent.left = self.NYT
        parent.right = leaf
        parent.weight = weight

        # updating the state variables
        self.symbol_catalogue[symbol] = leaf

        node_to_add = [leaf]
        if not parent.is_root:
            node_to_add = [leaf, parent]

        self.weight_catalogue[weight] = node_to_add + self.weight_catalogue[weight]

        self.order_index -= 2

        return parent

    @staticmethod
    def get_code(node: HuffmanNode) -> Bitcode:
        code = ""
        while node.parent != None:
            parent = node.parent
            code += "0" if parent.left is node else "1"
            node = parent

        return code[::-1]

    @staticmethod
    def relocate_node(node_1: HuffmanNode, node_2: HuffmanNode) -> None:
        # Things to swap:
        # 1. node's order
        # 2. node's parent pointer
        # 3. node's parent child pointer

        # i) all the children will remain as the node's children, so they dont need to be relocated
        # ii) weight and symbol is tied to the node, never to be relocated
        # iii) order needs to be changed as the order doesn't depend on the nodes,
        #      rather it depend son the position of said nodes

        node_1.order, node_2.order = node_2.order, node_1.order

        parent_1, parent_2 = node_1.parent, node_2.parent
        if parent_1 is parent_2:
            parent_1.left, parent_1.right = parent_1.right, parent_1.left
            return

        node_1.parent, node_2.parent = parent_2, parent_1
        setattr(parent_1, "left" if node_1 is parent_1.left else "right", node_2)
        setattr(parent_2, "left" if node_2 is parent_2.left else "right", node_1)


class AdaptiveHuffmanCodingEncoder(AdaptiveHuffmanTree):
    def __init__(self) -> None:
        super().__init__()

    def encode(self, data: str) -> Bitcode:
        huffman_code = ""
        try:
            for symbol in data:
                if symbol in self.symbol_catalogue:
                    node = self.symbol_catalogue[symbol]
                    huffman_code += self.get_code(node)

                else:
                    huffman_code += self.get_code(self.NYT) + FIXED_CODE_LOOKUP[symbol]

                    node = self.create_node(symbol)
                    if node.parent and not node.parent.is_root:
                        node = self.pre_process(node)

                self.update(node)
        except Exception as err:
            raise Exception("error occured while encoding") from err

        return huffman_code


class AdaptiveHuffmanCodingDecoder(AdaptiveHuffmanTree):
    def __init__(self) -> None:
        super().__init__()

    def decode(self, bits: Bitcode) -> str:
        symbol_getter = self.get_symbol(bits)
        decoded_data = ""
        try:
            while True:
                symbol = next(symbol_getter)

                if symbol is main_config.EOF_MARKER:
                    break

                elif symbol in self.symbol_catalogue:
                    node = self.symbol_catalogue[symbol]

                else:
                    node = self.create_node(symbol)

                    if node.parent and not node.parent.is_root:
                        node = self.pre_process(node)

                self.update(node)
                decoded_data += symbol

        except StopIteration:
            pass
            # raise Exception("error occured while decoding") from err

        return decoded_data

    def get_symbol(self, bits: Bitcode) -> str:
        if self.root is self.NYT:
            code, bits = bits[:FIXED_CODE_SIZE], bits[FIXED_CODE_SIZE:]
            yield FIXED_SYMBOL_LOOKUP[code]

        bitstream = iter(bits)
        current_node = self.root

        try:
            while True:

                new_bit = next(bitstream)
                if new_bit == "0":
                    current_node = current_node.left
                elif new_bit == "1":
                    current_node = current_node.right
                else:
                    raise ValueError(f"invalid bit found: {new_bit}")

                if current_node is self.NYT:
                    current_node = self.root
                    i = 0
                    buffer = ""
                    while i < FIXED_CODE_SIZE:
                        buffer += next(bitstream)
                        i += 1

                    yield FIXED_SYMBOL_LOOKUP[buffer]

                elif current_node.is_leaf:
                    symbol = current_node.symbol
                    current_node = self.root
                    yield symbol

        except StopIteration:
            pass


def encode() -> Generator[Bitcode, str, AdaptiveHuffmanTree]:
    tree = AdaptiveHuffmanTree()
    huffman_code = ""

    try:
        while True:
            symbol = yield huffman_code

            if symbol in tree.symbol_catalogue:
                node = tree.symbol_catalogue[symbol]
                huffman_code = tree.get_code(node)

            else:
                node = tree.create_node(symbol)
                huffman_code = tree.get_code(tree.NYT) + FIXED_CODE_LOOKUP[symbol]

                if node.parent and not node.parent.is_root:
                    node = tree.pre_process(node)

            tree.update(node)

    except Exception as err:
        raise Exception("error occured while encoding") from err


def generate_header_from_codebook(
    codebook: Dict[ValidData, Bitcode], dtype: SupportedDataType
) -> Tuple[Bitcode, Bitcode]:
    codelengths = ["0" * config.CODELENGTH_BITSIZE for _ in range(config.MAX_CODELENGTH)]
    counted_codelengths = Counter([len(code) for code in codebook.values()])

    for length, count in counted_codelengths.items():
        codelengths[length - 1] = tobin(count, config.CODELENGTH_DTYPE, bitlength=config.CODELENGTH_BITSIZE)

    codelengths = "".join(codelengths)
    symbols = tobin("".join(codebook.keys()) if dtype in ("s", str) else codebook.keys(), dtype)

    return codelengths, symbols


# ? wtf is happening here
def generate_codebook_from_dataset(dataset: ValidDataset = None) -> Dict[ValidData, Bitcode]:
    # putting the symbol in a list to allow concatenation for 'int' and 'float' during the 'tree building process'
    counted_dataset = Counter(dataset).most_common()

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


def generate_canonical_codebook(dataset: ValidDataset) -> Dict[ValidData, Bitcode]:
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

        canonical_codebook[symbol] = tobin(curr_code, "H", bitlength=bitlength)
        prev_bitlength = bitlength

    return canonical_codebook


def generate_codebook_from_header(header: Bitcode, dtype: SupportedDataType) -> Dict[Bitcode, ValidData]:
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
