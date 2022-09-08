import operator
import bisect
import dataclasses
import collections as colt
from typing import Dict, List

from pyencoder import Config


@dataclasses.dataclass
class AdaptiveHuffmanNode:
    symbol: str
    weight: int
    order: int = dataclasses.field(compare=True)

    parent: "AdaptiveHuffmanNode" = dataclasses.field(default=None, repr=False)
    left: "AdaptiveHuffmanNode" = dataclasses.field(default=None, repr=False)
    right: "AdaptiveHuffmanNode" = dataclasses.field(default=None, repr=False)

    @property
    def is_branch(self) -> bool:
        return self.parent is not None and self.symbol is None and self.weight > 0

    @property
    def is_leaf(self) -> bool:
        return self.symbol is not None and self.weight > 0

    @property
    def is_root(self) -> bool:
        return self.parent is None and self.symbol is None and self.weight > 0

    def __gt__(self, other: "AdaptiveHuffmanNode") -> bool:
        if self.order > other.order:
            if self.is_leaf and other.is_branch:
                return False
            return True
        if self.is_branch and other.is_leaf:
            return False
        return True

    def __lt__(self, other: "AdaptiveHuffmanNode") -> bool:
        if self.order < other.order:
            if self.is_branch and other.is_leaf:
                return False
            return True
        if self.is_leaf and other.is_branch:
            return True
        return False


def get_huffman_code(node: AdaptiveHuffmanNode) -> str:
    code = ""
    while node.parent != None:
        parent = node.parent
        code += "0" if parent.left is node else "1"
        node = parent

    return code[::-1]


def relocate_node(node_1: AdaptiveHuffmanNode, node_2: AdaptiveHuffmanNode) -> None:
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


class AdaptiveHuffmanTree:
    def __init__(self) -> None:
        self.reset()

    def reset(self) -> None:
        self.symbol_catalogue: Dict[str, AdaptiveHuffmanNode] = {}
        self.weight_catalogue: colt.OrderedDict[int, List[AdaptiveHuffmanNode]] = colt.OrderedDict({1: []})
        self.order_index = 2 * Config["NUM_SYMBOLS"] - 1

        self.root = self.NYT = AdaptiveHuffmanNode(None, 0, self.order_index)

    def increment_node_weight(self, node: AdaptiveHuffmanNode) -> None:
        # every time a node is promoted, the node is sorted into the list
        # thus, the list maintains sorted by 'order' at all times
        self.weight_catalogue[node.weight].remove(node)
        node.weight += 1
        weight_category = self.weight_catalogue.setdefault(node.weight, [])
        bisect.insort(weight_category, node, key=operator.attrgetter("order"))

    def pre_process(self, node: AdaptiveHuffmanNode) -> AdaptiveHuffmanNode:
        arr = self.weight_catalogue[node.weight]

        # * Note: the list is sorted by 'order' at all times
        # by definition the order of a child must be smaller than its parent
        # so if the node with the highest order is the node's parent
        # the next node with the highest order must be the node and thus no relocation is needed
        highest_order_node = arr[-1]
        node_original_parent = node.parent
        if highest_order_node not in (node, node.parent):
            relocate_node(node, highest_order_node)

            if node.weight == highest_order_node.weight:
                ind_1 = arr.index(node)
                ind_2 = arr.index(highest_order_node)
                arr[ind_1], arr[ind_2] = arr[ind_2], arr[ind_1]

        self.increment_node_weight(node_original_parent)

        return node.parent

    def update(self, node: AdaptiveHuffmanNode) -> None:
        while not node.is_root:

            arr = self.weight_catalogue[node.weight]

            # * Note: the list is sorted by 'order' at all times
            # by definition the order of a child must be smaller than its parent
            # so if the node with the highest order is the node's parent
            # the next node with the highest order must be the node and thus no relocation is needed
            highest_order_node = arr[-1]
            if highest_order_node not in (node, node.parent):
                relocate_node(node, highest_order_node)

            self.increment_node_weight(node)
            node = node.parent

    def create_node(self, symbol: str) -> AdaptiveHuffmanNode:
        # setting the NYT node as the parent and spawning two new children for it
        parent = self.NYT
        weight = 1

        leaf = AdaptiveHuffmanNode(symbol, weight, self.order_index - 1, parent)
        self.NYT = AdaptiveHuffmanNode(None, 0, self.order_index - 2, parent)

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
