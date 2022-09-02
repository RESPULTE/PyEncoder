import collections
import pyencoder.HuffmanCoding.codebook as hc
import uuid
import pytest


@pytest.fixture
def completed_tree(StringData) -> hc.AdaptiveHuffmanCodingEncoder:
    encoder = hc.AdaptiveHuffmanCodingEncoder()
    encoder.encode(StringData + hc.main_config.EOF_MARKER)
    return encoder


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


def test_parent_child_relation(completed_tree: hc.AdaptiveHuffmanCodingEncoder) -> None:
    def recursive_check(node: hc.HuffmanNode, parent: hc.HuffmanNode):
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
    tree = hc.AdaptiveHuffmanTree()
    old_NYT_node = tree.NYT
    parent_node = tree.create_node("ASS")
    leaf_node, NYT_node = parent_node.right, parent_node.left

    assert old_NYT_node is parent_node

    assert leaf_node.is_leaf and leaf_node.symbol is "ASS"

    assert leaf_node.order is (parent_node.order - 1)

    assert NYT_node is tree.NYT

    assert tree.order_index is tree.NYT.order


def test_generator_encode(StringData: str) -> None:
    encoder = hc.encode()

    encoder.send(None)
    for sym in StringData:
        encoder.send(sym)


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


def test_decode(StringData: str) -> None:
    encoder = hc.AdaptiveHuffmanCodingEncoder()
    encoded_data = encoder.encode(StringData + hc.main_config.EOF_MARKER)
    decoder = hc.AdaptiveHuffmanCodingDecoder()
    decoded_data = decoder.decode(encoded_data)
    assert decoded_data == StringData
