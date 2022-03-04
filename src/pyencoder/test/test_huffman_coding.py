import collections
import tempfile
import pytest
import os

from pyencoder import HuffmanCoding as hc
from pyencoder.HuffmanCoding import Huffman_Node


def dfs(node: Huffman_Node):
    if not isinstance(node, Huffman_Node):
        return [node]

    dataset = []
    if node.left is not None:
        dataset.extend(dfs(node.left))
    if node.right is not None:
        dataset.extend(dfs(node.right))

    return dataset


@pytest.mark.parametrize(
    "data",
    ["Never gonna give you up", [1, 1, 1, 2, 3, 5, 5, 5], [1.1, 1.111, 1.1, 45, 34, 45]],
    ids=["str", "int", "float"],
)
def test_build_tree_from_dataset(data):
    quantised_dataset = collections.Counter(data).most_common()
    huffman_tree = hc.build_tree_from_dataset(quantised_dataset)
    assert set(dfs(huffman_tree)) == set(data)


def test_generate_catalogue(StringData):
    quantised_dataset = collections.Counter(StringData).most_common()
    min_freq = min(quantised_dataset, key=lambda data: data[1])[1]
    max_freq = max(quantised_dataset, key=lambda data: data[1])[1]
    data_with_min_freq = [data for data, freq in quantised_dataset if freq == min_freq]
    data_with_max_freq = [data for data, freq in quantised_dataset if freq == max_freq]

    huffman_tree = hc.build_tree_from_dataset(quantised_dataset)
    catalogue = hc.generate_catalogue(huffman_tree)

    sorted_huffcode = sorted(list(catalogue.keys()), key=lambda huffcode: len(huffcode))
    sorted_encoded_data = [catalogue[huffcode] for huffcode in sorted_huffcode]

    encoded_data_with_max_freq = sorted_encoded_data[: len(data_with_max_freq)]
    encoded_data_with_min_freq = sorted_encoded_data[: -len(data_with_min_freq) : -1]

    assert set(encoded_data_with_max_freq).issubset(set(data_with_max_freq))
    assert set(encoded_data_with_min_freq).issubset(set(data_with_min_freq))


def test_encode():
    catalogue = {"k": "0", "o": "11", "c": "69"}
    assert hc.encode_dataset("cock", catalogue) == "6911690"


def test_dump_load():
    with tempfile.TemporaryDirectory() as td:
        tmp = os.path.join(td, "test")
        with open(tmp, "wb") as f:
            hc.dump("lmao noob", f)

        with open(tmp, "rb") as f:
            loaded_data = hc.load(f)

        assert loaded_data == "lmao noob"
