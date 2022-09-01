import collections
import pyencoder.HuffmanCoding.codebook as hc
import uuid
import pytest


@pytest.fixture
def completed_tree(StringData) -> hc.AdaptiveHuffmanTree:
    tree = hc.AdaptiveHuffmanTree()
    for sym in StringData:
        tree.encode(sym)

    return tree


def test_relocate_node() -> None:
    uid = uuid.uuid1

    # None for all cuz they wont be compared
    parent_1 = hc.HuffmanNode(None, 1000, None, None)
    parent_2 = hc.HuffmanNode(None, 1000, None, None)

    # using uuid cuz the type of them doesn't matter
    symbol_1, symbol_2 = uid(), uid()
    weight_1, weight_2 = 100, 120
    order_1, order_2 = uid(), uid()
    child_l1, child_r1 = uid(), uid()
    child_l2, child_r2 = uid(), uid()

    node_1 = hc.HuffmanNode(symbol_1, weight_1, order_1, parent_1, child_l1, child_r1)
    node_2 = hc.HuffmanNode(symbol_2, weight_2, order_2, parent_2, child_l2, child_r2)

    # setting the parent-to-child relationshi[]
    parent_1.left = node_1
    parent_2.right = node_2

    hc.AdaptiveHuffmanTree.relocate_node(node_1, node_2)

    # check parent correctness
    assert node_1.parent is parent_2 and node_2.parent is parent_1

    # # check parent's child correctness
    assert parent_1.left is node_2 and parent_2.right is node_1

    # check order correctness
    assert node_1.order is order_2 and node_2.order is order_1


def test_create_node() -> None:
    # populating tree with some random nodes (test for the insertion)
    tree = hc.AdaptiveHuffmanTree()
    tree.create_node("initial")

    symbol = "ASS"
    node = tree.create_node(symbol)

    assert node.order == (node.parent.order - 1)

    # test order update correctness
    assert tree.NYT.order == (node.parent.order - 2) == tree.order_index

    # test parent-to-child relation correctness
    assert node.parent.left == tree.NYT and node.parent.right == node

    assert symbol in tree.symbol_catalogue

    # test cataloguing correctness
    assert tree.weight_catalogue[1][0:2] == [node, node.parent]


def test_get_code() -> None:
    n1 = hc.HuffmanNode(None, None, None)
    n2 = hc.HuffmanNode(None, None, None, n1)
    n3 = hc.HuffmanNode(None, None, None, n2)
    n4 = hc.HuffmanNode(None, None, None, n3)
    n5 = hc.HuffmanNode(None, None, None, n4)

    n1.right = n2
    n2.left = n3
    n3.right = n4
    n4.right = n5

    assert hc.AdaptiveHuffmanTree.get_code(n5) == "1011"


def test_symbol_weight_correctness(StringData: int, completed_tree: hc.AdaptiveHuffmanTree) -> None:
    for sym, count in collections.Counter(StringData).most_common():
        node = completed_tree.symbol_catalogue[sym]
        assert node.weight == count


def test_set_node_weight() -> None:
    tree = hc.AdaptiveHuffmanTree()
    node = hc.HuffmanNode(None, 1, 249)

    tree.weight_catalogue[2] = [hc.HuffmanNode(None, 2, 224), hc.HuffmanNode(None, 2, 250)]
    tree.weight_catalogue[1] = [node]

    tree.increment_node_weight(node)

    assert tree.weight_catalogue[2][1] is node

    assert node.weight == 2
