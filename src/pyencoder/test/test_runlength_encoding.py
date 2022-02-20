import tempfile
import pytest
import os

from pyencoder import RunLengthEncoding as rle


@pytest.mark.parametrize(
    "dataset, dtype, expected",
    [
        (
            [1, 1, 1, 1, 1, 1, 1, 1, 2, 2, 2, 3, 4, 5, 6, 3, 3, 5],
            int,
            "1|8|2|3|3|1|4|1|5|1|6|1|3|2|5|1",
        ),
        ("nnnnnneeeeevvvveerrrrr", str, "n|6|e|5|v|4|e|2|r|5"),
    ],
    ids=["int", "str"],
)
def test_encoding(dataset, dtype, expected):
    assert rle.encode(dataset, dtype) == expected


def test_decoding(StringData):
    assert rle.decode(rle.encode(StringData, str), str) == StringData


def test_dump_load():
    with tempfile.TemporaryDirectory() as td:
        tmp = os.path.join(td, "test")
        with open(tmp, "wb") as f:
            rle.dump("lmao noob", f, str)

        with open(tmp, "rb") as f:
            loaded_data = rle.load(f)

        assert loaded_data == "lmao noob"

