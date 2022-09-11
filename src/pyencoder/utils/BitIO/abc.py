import abc
from typing import BinaryIO
from pyencoder.utils.BitIO import BUFFER_BITSIZE
from pyencoder.utils.bitbuffer import BitIntegerBuffer, BitStringBuffer


class IBufferedBitIO(abc.ABC):
    def __init__(self, file_obj: BinaryIO, buffer_size: int = BUFFER_BITSIZE) -> None:
        self.file_obj = file_obj
        self.buffer_size = buffer_size

        self.buffer: BitIntegerBuffer | BitStringBuffer = None
        self._flushed = False

    @property
    def flushed(self) -> bool:
        return self._flushed

    @abc.abstractmethod
    def flush(self) -> None:
        ...

    def __bool__(self) -> bool:
        return not self._flushed


class IBufferedBitTypeIO(IBufferedBitIO):
    @abc.abstractmethod
    def _convert_to_bytes(self, data) -> bytes:
        ...


class IBufferedBitInput(IBufferedBitIO):
    @abc.abstractmethod
    def read(self, n: int) -> int | str:
        ...


class IBufferedBitOutput(IBufferedBitIO):
    @abc.abstractmethod
    def write(self, bits: int | str) -> None:
        ...

    @abc.abstractmethod
    def _resolve_incomplete_bytes(self) -> None:
        ...

    @abc.abstractmethod
    def _convert_to_bytes(self, data) -> bytes:
        ...
