import tempfile
import pytest
import os

from pyencoder import HuffmanCoding as hc


def test_dump_load():
    with tempfile.TemporaryDirectory() as td:
        tmp = os.path.join(td, "test")
        with open(tmp, "wb") as f:
            hc.dump("lmao noob", f)

        with open(tmp, "rb") as f:
            loaded_data = hc.load(f)

        assert loaded_data == "lmao noob"
