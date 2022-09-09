import abc
import functools
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


class IBufferedBitInput(IBufferedBitIO):
    def __init__(self, source_obj: BinaryIO | str | bytes, buffer_size: int = BUFFER_BITSIZE) -> None:
        super().__init__(source_obj, buffer_size)

        if hasattr(self.source_obj, "read"):
            self.source_reader = functools.partial(self.source_obj.read, buffer_size // 8)

        elif isinstance(self.source_obj, str):
            reader = functools.partial(slice_read, self.source_obj, self.buffer_size)()
            self.source_reader = lambda: next(reader)

        elif isinstance(self.source_obj, bytes):
            reader = functools.partial(slice_read, self.source_obj, buffer_size // 8)()
            self.source_reader = lambda: next(reader)

        else:
            raise TypeError("invalid type: {0}".format(type(self.source_obj).__name__))

    def read(self, n: int) -> int | str:
        # if reading process is finished
        if self._flushed or n <= 0:
            return None

        # if the bits left in the buffer is more than the requested amount
        if n <= self.buffered_size:
            return self._read_from_buffer(n)

        while self.buffered_size < n:
            source_data = self.source_reader()

            if not source_data:
                return self.flush()

            buffered_bits = self._convert_to_retval(source_data)
            self.buffer(buffered_bits)

        return self._read_from_buffer(n)

    def flush(self) -> str:
        retval = self.buffered_bits
        self.buffered_bits = None
        self._flushed = True
        return retval

    def buffer(self, bits: str | int) -> None:
        # if the current buffer still hasn't been exhausted
        if self.buffered_size:
            self._write_to_buffer(bits)
            return

        # if the current buffer has been exhausted
        self.buffered_bits = bits
        self.buffered_size = len(bits)

    @abc.abstractmethod
    def _convert_to_retval(self, data: bytes | str) -> str | int:
        ...

    def __bool__(self) -> bool:
        return not self._flushed


class IBufferedBitOutput(IBufferedBitIO):
    def __init__(self, file_obj: BinaryIO, buffer_size: int = BUFFER_BITSIZE) -> None:
        super().__init__(file_obj, buffer_size)

    def write(self, bits: int | str) -> None:
        self._write_to_buffer(bits)

        if self.buffered_size < self.buffer_size:
            return

        while self.buffered_size > self.buffer_size:
            retval = self._read_from_buffer(self.buffer_size)
            bytes_to_output = self._convert_to_bytes(retval)
            self.source_obj.write(bytes_to_output)

    def flush(self) -> None:
        self._resolve_incomplete_bytes()
        bytes_to_output = self._convert_to_bytes(self.buffered_bits)
        self.source_obj.write(bytes_to_output)

        self.buffered_bits = None
        self._flushed = True

    @abc.abstractmethod
    def _convert_to_bytes(self) -> bytes:
        ...

    @abc.abstractmethod
    def _resolve_incomplete_bytes(self) -> None:
        ...
