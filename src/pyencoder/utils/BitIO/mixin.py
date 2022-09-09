from typing import BinaryIO

from pyencoder.utils.BitIO.abc import IBufferedBitIO
from pyencoder.utils.BitIO import BUFFER_BITSIZE
from pyencoder.utils.bitInteger import BitInteger

from pyencoder.utils.binary import *


class MixinBufferedIntegerIO(IBufferedBitIO):
    def __init__(self, source_obj: BinaryIO | bytes | str, buffer_size: int = BUFFER_BITSIZE) -> None:
        super().__init__(source_obj, buffer_size)
        self.buffered_bits = BitInteger("0")

    def _convert_to_retval(self, data: bytes | str) -> BitInteger:
        return BitInteger(data)

    def _convert_to_bytes(self, data: BitInteger) -> bytes:
        return convert_ints_to_bytes(data, data.size)

    def _resolve_incomplete_bytes(self) -> None:
        size = 8 - self.buffered_size % 8
        if size == 8:
            return
        self.buffered_bits <<= size
        self.buffered_size += size

    def _read_from_buffer(self, n: int) -> BitInteger:
        retval, self.buffered_bits = self.buffered_bits.lslice(n)
        self.buffered_size -= n
        return retval

    def _write_to_buffer(self, bits: int) -> None:
        bits_size = len(bits)
        self.buffered_bits = (self.buffered_bits << bits_size) | bits
        self.buffered_size += bits_size


class MixinBufferedStringIO(IBufferedBitIO):
    def __init__(self, source_obj: BinaryIO | str | bytes, buffer_size: int = BUFFER_BITSIZE) -> None:
        super().__init__(source_obj, buffer_size)
        self.buffered_bits = ""

        if isinstance(source_obj, str):
            self._convert_to_retval = lambda x: x

    def _convert_to_retval(self, data: str | bytes) -> str:
        return convert_bytes_to_bits(data, len(data) * 8)

    def _convert_to_bytes(self, data: str) -> bytes:
        return convert_bits_to_bytes(data, -(-len(data) // 8))

    def _resolve_incomplete_bytes(self) -> None:
        size = 8 - self.buffered_size % 8
        if size == 8:
            return
        self.buffered_bits += "0" * size
        self.buffered_size += size

    def _read_from_buffer(self, n: int) -> str:
        self.buffered_size -= n
        retval = self.buffered_bits[:n]
        self.buffered_bits = self.buffered_bits[n:]
        return retval

    def _write_to_buffer(self, bits: str) -> None:
        self.buffered_bits += bits
        self.buffered_size += len(bits)
