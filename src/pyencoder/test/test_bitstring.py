import pytest

from pyencoder.utils.bitstring import BitInteger


def test_creation():
    with pytest.raises(TypeError):
        BitInteger(10.11, int)


@pytest.mark.parametrize("val", [bytes([0]), bytes([100]), bytes([255, 225, 255])])
def test_iteration_int(val: int):
    bs = BitInteger(val)
    buffer = 0
    for i in bs:
        buffer = (buffer << 1) | i

    assert buffer == bs
