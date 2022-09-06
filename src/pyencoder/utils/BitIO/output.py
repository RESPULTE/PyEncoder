import abc
from typing import BinaryIO, Union


from pyencoder.utils.BitIO.abc import IBufferedBitIO, IBufferedIntegerIO, IBufferedStringIO
from pyencoder.utils.BitIO.config import BUFFER_BYTE_SIZE


class IBufferedBitOutput(IBufferedBitIO):
    def __init__(self, file_obj: BinaryIO, buffer_size: int = BUFFER_BYTE_SIZE) -> None:
        super().__init__(file_obj, buffer_size)

    def write(self, bits: int | str) -> None:
        self._write_to_buffer(bits)

        if self.buffered_size < self.bit_buffer_size:
            return

        retval = self._read_from_buffer(self.bit_buffer_size)
        bytes_to_output = self._convert_to_bytes(retval)
        self.source_obj.write(bytes_to_output)

    @abc.abstractmethod
    def _convert_to_bytes(self) -> bytes:
        ...

    def flush(self) -> None:
        if self.buffered_size != 0:
            self.byte_buffer_size = -(-self.buffered_size // 8)
            bytes_to_output = self._convert_to_bytes(self.buffered_bits)
            self.source_obj.write(bytes_to_output)

        self.buffered_size = 0
        self.buffered_bits = None
        self._flushed = True


def BufferedBitOutput(
    file_obj: BinaryIO, buffer_size: int = BUFFER_BYTE_SIZE, as_int: bool = False
) -> Union["BufferedIntegerOutput", "BufferedStringOutput"]:
    cls = BufferedStringOutput if not as_int else BufferedIntegerOutput

    return cls(file_obj, buffer_size)


class BufferedStringOutput(IBufferedStringIO, IBufferedBitOutput):
    def __init__(self, file_obj: BinaryIO, buffer_size: int = BUFFER_BYTE_SIZE) -> None:
        super().__init__(file_obj, buffer_size)


class BufferedIntegerOutput(IBufferedIntegerIO, IBufferedBitOutput):
    def __init__(self, file_obj: BinaryIO, buffer_size: int = BUFFER_BYTE_SIZE) -> None:
        super().__init__(file_obj, buffer_size)
