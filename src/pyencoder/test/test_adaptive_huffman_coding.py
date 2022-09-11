import uuid
import pytest
import collections

from pyencoder.HuffmanCoding import AdaptiveHuffmanCoding
import pyencoder.HuffmanCoding.AdaptiveHuffmanCoding.codebook as codebook


@pytest.fixture
def completed_tree(StringData) -> AdaptiveHuffmanCoding.AdaptiveEncoder:
    encoder = AdaptiveHuffmanCoding.AdaptiveEncoder()
    for sym in StringData:
        encoder.encode(sym)
    encoder.flush()
    return encoder


def test_relocate_node() -> None:
    uid = uuid.uuid1

    # None for all cuz they wont be compared
    parent_1 = codebook.AdaptiveHuffmanNode(None, 1000, None, None)
    parent_2 = codebook.AdaptiveHuffmanNode(None, 1000, None, None)

    # using uuid cuz the type of them doesn't matter
    symbol_1, symbol_2 = uid(), uid()
    weight_1, weight_2 = 100, 120
    order_1, order_2 = uid(), uid()
    child_l1, child_r1 = uid(), uid()
    child_l2, child_r2 = uid(), uid()

    node_1 = codebook.AdaptiveHuffmanNode(symbol_1, weight_1, order_1, parent_1, child_l1, child_r1)
    node_2 = codebook.AdaptiveHuffmanNode(symbol_2, weight_2, order_2, parent_2, child_l2, child_r2)

    # setting the parent-to-child relationshi[]
    parent_1.left = node_1
    parent_2.right = node_2

    codebook.relocate_node(node_1, node_2)

    # check parent correctness
    assert node_1.parent is parent_2 and node_2.parent is parent_1

    # # check parent's child correctness
    assert parent_1.left is node_2 and parent_2.right is node_1

    # check order correctness
    assert node_1.order is order_2 and node_2.order is order_1


def test_parent_child_relation(completed_tree: AdaptiveHuffmanCoding.AdaptiveEncoder) -> None:
    def recursive_check(node: codebook.AdaptiveHuffmanNode, parent: codebook.AdaptiveHuffmanNode):
        if node.left:
            assert recursive_check(node.left, node) is True, "invalid child to parent relation"
        if node.right:
            assert recursive_check(node.right, node) is True, "invalid child to parent relation"

        if node.parent is not None:
            assert node in (parent.left, parent.right), "invalid parent to child relation"
        else:
            assert not node.is_branch and not node.is_leaf, "invalid root node"

        return node.parent is parent and node.parent not in (node, node.left, node.right)

    return recursive_check(completed_tree.root, None)


def test_create_node() -> None:
    # populating tree with some random nodes (test for the insertion)
    tree = AdaptiveHuffmanCoding.AdaptiveHuffmanTree()
    old_NYT_node = tree.NYT
    parent_node = tree.create_node("ASS")
    leaf_node, NYT_node = parent_node.right, parent_node.left

    assert old_NYT_node is parent_node

    assert leaf_node.is_leaf and leaf_node.symbol is "ASS"

    assert leaf_node.order is (parent_node.order - 1)

    assert NYT_node is tree.NYT

    assert tree.order_index is tree.NYT.order


def test_get_code() -> None:
    n1 = codebook.AdaptiveHuffmanNode(None, None, None)
    n2 = codebook.AdaptiveHuffmanNode(None, None, None, n1)
    n3 = codebook.AdaptiveHuffmanNode(None, None, None, n2)
    n4 = codebook.AdaptiveHuffmanNode(None, None, None, n3)
    n5 = codebook.AdaptiveHuffmanNode(None, None, None, n4)

    n1.right = n2
    n2.left = n3
    n3.right = n4
    n4.right = n5

    assert codebook.get_huffman_code(n5) == "1011"


def test_symbol_weight_correctness(StringData: int, completed_tree: AdaptiveHuffmanCoding.AdaptiveHuffmanTree) -> None:
    for sym, count in collections.Counter(StringData).most_common():
        node = completed_tree.symbol_catalogue[sym]
        assert node.weight == count


def test_set_node_weight() -> None:
    tree = AdaptiveHuffmanCoding.AdaptiveHuffmanTree()
    node = codebook.AdaptiveHuffmanNode(None, 1, 249)

    tree.weight_catalogue[2] = [codebook.AdaptiveHuffmanNode(None, 2, 224), codebook.AdaptiveHuffmanNode(None, 2, 250)]
    tree.weight_catalogue[1] = [node]

    tree.increment_node_weight(node)

    assert tree.weight_catalogue[2][1] is node

    assert node.weight == 2
