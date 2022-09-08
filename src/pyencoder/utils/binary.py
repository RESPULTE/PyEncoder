from typing import Iterable
from pyencoder import Config


def convert_bits_to_bytes(bits: str, size: int = 0) -> bytes:
    return int.to_bytes(int(bits, 2), size or -(-len(bits) // 8), Config["ENDIAN"])


def convert_bytes_to_bits(_bytes: bytes, size: int = 0) -> str:
    return "{num:0{bit_size}b}".format(num=int.from_bytes(_bytes, Config["ENDIAN"]), bit_size=size)


def convert_ints_to_bytes(_ints: int, size: int = 0) -> bytes:
    return int.to_bytes(_ints, size or -(-_ints.bit_length() // 8), Config["ENDIAN"])


def convert_bytes_to_ints(_bytes: bytes) -> int:
    return int.from_bytes(_bytes, Config["ENDIAN"])


def convert_from_bits_to_ints(bits: str) -> int:
    return int(bits, 2)


def slice_read(source: str | bytes, n: int) -> Iterable[str | bytes]:
    index = 0
    while True:
        yield source[index : index + n]
        index += n
