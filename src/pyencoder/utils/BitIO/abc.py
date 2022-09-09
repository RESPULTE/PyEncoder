import abc
from typing import BinaryIO
from pyencoder.utils.BitIO import BUFFER_BITSIZE

from pyencoder.utils.binary import *


class IBufferedBitIO(abc.ABC):
    def __init__(self, source_obj: BinaryIO, buffer_size: int = BUFFER_BITSIZE) -> None:
        self.source_obj = source_obj
        self.buffer_size = buffer_size

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
