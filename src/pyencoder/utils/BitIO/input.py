import abc
from typing import BinaryIO, Union, Literal, Iterable

from pyencoder.utils.BitIO.abc import IBufferedBitIO, IBufferedIntegerIO, IBufferedStringIO
from pyencoder.utils.BitIO.config import BUFFER_BYTE_SIZE


class IBufferedBitInput(IBufferedBitIO):
    def __init__(self, file_obj: BinaryIO, buffer_size: int = BUFFER_BYTE_SIZE) -> None:
        super().__init__(file_obj, buffer_size)

    def read(self) -> int | str:
        # if the bits left in the buffer is more than the requested amount
        if self.buffered_size > 0:
            return self.read_from_buffer(1)

        elif self._flushed and self.buffered_size == 0:
            return None

        buffered_bytes = self.file_obj.read(self.byte_buffer_size)

        # if the file has been exhausted
        byte_size = len(buffered_bytes)
        if byte_size < self.byte_buffer_size:
            self.byte_buffer_size = byte_size
            self.bit_buffer_size = byte_size * 8
            self._flushed = True

        new_bits = self._convert_from_bytes(buffered_bytes)
        self.write_to_buffer(new_bits)

        return self.read_from_buffer(1)

    @abc.abstractmethod
    def _convert_from_bytes(self, _bytes: bytes, size: int) -> str | int:
        ...


def BufferedBitInput(
    file_obj: BinaryIO, buffer_size: int = BUFFER_BYTE_SIZE, as_int: bool = False
) -> Union["BufferedBitIntegerInput", "BufferedStringInput"]:

    cls = BufferedStringInput if not as_int else BufferedBitIntegerInput
    return cls(file_obj, buffer_size)


class BufferedStringInput(IBufferedStringIO, IBufferedBitInput):
    def __init__(self, file_obj: BinaryIO, buffer_size: int = BUFFER_BYTE_SIZE) -> None:
        super().__init__(file_obj, buffer_size)

    def __iter__(self) -> Iterable[Literal["0", "1"]]:
        # python automatically converts bytes into a sequence of 8 bit integer when it is iterated
        for b in self.file_obj.read():
            bits = "{0:08b}".format(b)
            for i in range(0, 8):
                yield bits[i]


class BufferedBitIntegerInput(IBufferedIntegerIO, IBufferedBitInput):
    def __init__(self, file_obj: BinaryIO, buffer_size: int = BUFFER_BYTE_SIZE) -> None:
        super().__init__(file_obj, buffer_size)

    def __iter__(self) -> Iterable[Literal[0, 1]]:
        # python automatically converts bytes into a sequence of 8 bit integer when it is iterated
        for b in self.file_obj.read():
            for i in range(1, 9):
                yield (b >> (8 - i)) & 1
