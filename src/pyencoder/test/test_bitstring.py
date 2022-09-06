import pytest

from typing import Type
from pyencoder.utils.BitIO.bitstring import Bitstring


def test_cache():
    test_2 = Bitstring(b"120", str)
    test_1 = Bitstring(b"120", str)
    assert test_1 is test_2


def test_creation():
    with pytest.raises(TypeError):
        Bitstring(10.11, int)


@pytest.mark.parametrize("val", [bytes([0]), bytes([100]), bytes([255, 255, 255])])
def test_iteration_int(val: int):
    bs = Bitstring(val, int)
    buffer = 0
    for i in bs:
        buffer = (buffer << 1) | i

    assert buffer == bs.data


@pytest.mark.parametrize("val", [b"", b"A", b"ASS"])
def test_iteration_str(val: int):
    bs = Bitstring(val, str)
    buffer = ""
    for i in bs:
        buffer += i

    assert buffer == bs.data


@pytest.mark.parametrize(["val", "retval"], [(b"10", int), (b"10", str)])
def test_retval(val: bytes, retval: Type[int] | Type[int]):
    bs = Bitstring(val, retval)

    for i in bs:
        length = i.bit_length() if isinstance(i, int) else len(i)
        assert isinstance(i, retval) and length in (0, 1)
