import abc
import io
from typing import BinaryIO, Union, Literal, Iterable

from pyencoder.utils.BitIO.abc import IBufferedBitIO, IBufferedIntegerIO, IBufferedStringIO
from pyencoder.utils.BitIO import BUFFER_BYTE_SIZE


class IBufferedBitInput(IBufferedBitIO):
    def __init__(self, source_obj: BinaryIO, buffer_size: int = BUFFER_BYTE_SIZE) -> None:
        super().__init__(source_obj, buffer_size)

        if hasattr(self.source_obj, "read"):
            self.bits_reader = self.read_from_file()

        elif isinstance(source_obj, str):
            self.bits_reader = self.read_from_bits()

        elif isinstance(source_obj, bytes):
            self.bits_reader = self.read_from_bytes()

        else:
            raise TypeError(f"invalid type for source object: {type(self.source_obj).__name__}")

    def read(self, n: int) -> int | str:
        # if reading process is finished
        if self._flushed or n <= 0:
            return None

        # if the bits left in the buffer is more than the requested amount
        if n < self.buffered_size:
            return self._read_from_buffer(n)

        while self.buffered_size < n:
            buffered_bits = next(self.bits_reader)
            if not buffered_bits:
                return self.flush()

            self.update_buffer(buffered_bits)

        return self._read_from_buffer(n)

    def flush(self) -> str:
        retval = self.buffered_bits
        self.buffered_bits = None
        self._flushed = True
        return retval

    def update_buffer(self, bits: str) -> None:
        # if the current buffer still hasn't been exhausted
        if self.buffered_size:
            self._write_to_buffer(bits)
            return

        # if the current buffer has been exhausted
        self.buffered_bits = bits
        self.buffered_size = self.bit_buffer_size

    def read_from_file(self) -> str:
        while True:
            byte = self.source_obj.read(self.byte_buffer_size)
            byte_size = len(byte)

            if byte_size == 0:
                yield ""

            elif byte_size < self.byte_buffer_size:
                self.byte_buffer_size = byte_size
                self.bit_buffer_size = byte_size * 8

            yield self._convert_from_bytes(byte)

    def read_from_bytes(self) -> str:
        index = 0
        reading = True
        while reading:

            byte_slice = self.source_obj[index : index + self.byte_buffer_size]
            byte_size = len(byte_slice)

            if byte_size == 0:
                yield ""

            elif byte_size < self.byte_buffer_size:
                self.byte_buffer_size = byte_size
                self.bit_buffer_size = byte_size * 8

            yield self._convert_from_bytes(byte_slice)

            index += self.byte_buffer_size

    def read_from_bits(self) -> str:
        index = 0
        reading = True
        while reading:

            bit_slice = self.source_obj[index : index + self.bit_buffer_size]
            bit_size = len(bit_slice)

            if bit_size == 0:
                yield ""

            elif bit_size < self.bit_buffer_size:
                self.byte_buffer_size = bit_size // 8
                self.bit_buffer_size = bit_size

            yield bit_slice

            index += self.bit_buffer_size

    def __bool__(self) -> bool:
        return not self._flushed

    @abc.abstractmethod
    def _convert_from_bytes(self, _bytes: bytes) -> str | int:
        ...


def BufferedBitInput(
    source_obj: BinaryIO, buffer_size: int = BUFFER_BYTE_SIZE, as_int: bool = False
) -> Union["BufferedIntegerInput", "BufferedStringInput"]:
    if isinstance(source_obj, (BufferedIntegerInput, BufferedStringInput)):
        return source_obj

    cls = BufferedStringInput if not as_int else BufferedIntegerInput
    return cls(source_obj, buffer_size)


class BufferedStringInput(IBufferedStringIO, IBufferedBitInput):
    def __init__(self, source_obj: BinaryIO, buffer_size: int = BUFFER_BYTE_SIZE) -> None:
        super().__init__(source_obj, buffer_size)

    def __iter__(self) -> Iterable[Literal["0", "1"]]:
        # python automatically converts bytes into a sequence of 8 bit integer when it is iterated
        for b in self.source_obj.read():
            bits = "{0:08b}".format(b)
            for i in range(0, 8):
                yield bits[i]


class BufferedIntegerInput(IBufferedIntegerIO, IBufferedBitInput):
    def __init__(self, source_obj: BinaryIO, buffer_size: int = BUFFER_BYTE_SIZE) -> None:
        super().__init__(source_obj, buffer_size)

    def __iter__(self) -> Iterable[Literal[0, 1]]:
        # python automatically converts bytes into a sequence of 8 bit integer when it is iterated
        for b in self.source_obj.read():
            for i in range(1, 9):
                yield (b >> (8 - i)) & 1
