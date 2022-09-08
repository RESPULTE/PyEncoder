import functools
from typing import BinaryIO, Union, Literal, Iterable

from pyencoder.utils.BitIO.abc import IBufferedBitIO, IBufferedIntegerIO, IBufferedStringIO
from pyencoder.utils.binary import slice_read
from pyencoder.utils.BitIO import BUFFER_BITSIZE


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
            return self.default_value

        # if the bits left in the buffer is more than the requested amount
        if n <= self.buffered_size:
            return self._read_from_buffer(n)

        while self.buffered_size < n:
            source_data = self.source_reader()

            if not source_data:
                return self.flush()

            buffered_bits = self._convert_to_retval(source_data)
            self.update_buffer(buffered_bits)

        return self._read_from_buffer(n)

    def flush(self) -> str:
        retval = self.buffered_bits
        self.buffered_bits = None
        self._flushed = True
        return retval

    def update_buffer(self, bits: str | int) -> None:
        # if the current buffer still hasn't been exhausted
        if self.buffered_size:
            self._write_to_buffer(bits)
            return

        # if the current buffer has been exhausted
        self.buffered_bits = bits
        self.buffered_size = len(bits)

    def _convert_to_retval(self, data: bytes | str) -> str | int:
        ...

    def __bool__(self) -> bool:
        return not self._flushed


def BufferedBitInput(
    source_obj: BinaryIO, buffer_size: int = BUFFER_BITSIZE, as_int: bool = False, default_value: str | int = None
) -> Union["BufferedIntegerInput", "BufferedStringInput"]:
    if isinstance(source_obj, (BufferedIntegerInput, BufferedStringInput)):
        return source_obj

    cls = BufferedStringInput if not as_int else BufferedIntegerInput
    return cls(source_obj, buffer_size, default_value)


class BufferedStringInput(IBufferedStringIO, IBufferedBitInput):
    def __init__(self, source_obj: BinaryIO, buffer_size: int = BUFFER_BITSIZE, default_value: str = None) -> None:
        super().__init__(source_obj, buffer_size)
        self.default_value = default_value

    def __iter__(self) -> Iterable[Literal["0", "1"]]:
        # python automatically converts bytes into a sequence of 8 bit integer when it is iterated
        for b in self.source_obj.read():
            bits = "{0:08b}".format(b)
            for i in range(0, 8):
                yield bits[i]


class BufferedIntegerInput(IBufferedIntegerIO, IBufferedBitInput):
    def __init__(self, source_obj: BinaryIO, buffer_size: int = BUFFER_BITSIZE, default_value: int = None) -> None:
        super().__init__(source_obj, buffer_size)
        self.default_value = default_value

    def __iter__(self) -> Iterable[Literal[0, 1]]:
        # python automatically converts bytes into a sequence of 8 bit integer when it is iterated
        for b in self.source_obj.read():
            for i in range(1, 9):
                yield (b >> (8 - i)) & 1
