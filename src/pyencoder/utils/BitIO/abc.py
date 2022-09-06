import abc
from typing import BinaryIO, TypeVar

from pyencoder.config.main_config import ENDIAN
from pyencoder.utils.BitIO.config import BUFFER_BYTE_SIZE
from pyencoder.utils.BitIO.bitstring import Bitstring

_T = TypeVar("_T")


class IBufferedBitIO(abc.ABC):
    def __init__(self, source_obj: BinaryIO, buffer_size: int = BUFFER_BYTE_SIZE) -> None:
        self.source_obj = source_obj

        self.byte_buffer_size = buffer_size
        self.bit_buffer_size = buffer_size * 8

        self.buffered_size = 0
        self.buffered_bits = None

        self._flushed = False

    @property
    def flushed(self) -> bool:
        return self._flushed

    @abc.abstractmethod
    def _read_from_buffer(self, n: int) -> int | str:
        ...

    @abc.abstractmethod
    def _write_to_buffer(self, bits: int | str) -> None:
        ...


class IBufferedIntegerIO(IBufferedBitIO):
    def __init__(self, source_obj: BinaryIO, buffer_size: int = BUFFER_BYTE_SIZE) -> None:
        super().__init__(source_obj, buffer_size)
        self.buffered_bits = 0

    def _read_from_buffer(self, n: int) -> int:
        index_from_left = self.buffered_size - n
        retval = (self.buffered_bits & (((1 << n) - 1) << index_from_left)) >> index_from_left
        self.buffered_bits = self.buffered_bits & ((1 << index_from_left) - 1)
        self.buffered_size -= n
        return retval

    def _write_to_buffer(self, bits: int) -> None:
        self.buffered_bits = (self.buffered_bits << self.bit_buffer_size) | bits
        self.buffered_size += self.bit_buffer_size

    def _convert_to_bytes(self, bits: int) -> bytes:
        return int.to_bytes(bits, self.byte_buffer_size, ENDIAN)

    def _convert_from_bytes(self, _bytes: bytes) -> int:
        return int.from_bytes(_bytes, ENDIAN)


class IBufferedStringIO(IBufferedBitIO):
    def __init__(self, source_obj: BinaryIO, buffer_size: int = BUFFER_BYTE_SIZE) -> None:
        super().__init__(source_obj, buffer_size)
        self.buffered_bits = ""

    def _read_from_buffer(self, n: int) -> str:
        self.buffered_size -= n
        retval = self.buffered_bits[:n]
        self.buffered_bits = self.buffered_bits[n:]
        return retval

    def _write_to_buffer(self, bits: str) -> None:
        self.buffered_bits += bits
        self.buffered_size += len(bits)

    def _convert_to_bytes(self, bits: str) -> bytes:
        return int.to_bytes(int(bits, 2), self.byte_buffer_size, ENDIAN)

    def _convert_from_bytes(self, _bytes: bytes) -> str:
        return "{num:0{bit_size}b}".format(num=int.from_bytes(_bytes, ENDIAN), bit_size=self.bit_buffer_size)
