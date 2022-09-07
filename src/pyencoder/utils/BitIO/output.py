import abc
from typing import BinaryIO, Union


from pyencoder.utils.BitIO.abc import IBufferedBitIO, IBufferedIntegerIO, IBufferedStringIO
from pyencoder.utils.BitIO import BUFFER_BYTE_SIZE


class IBufferedBitOutput(IBufferedBitIO):
    def __init__(self, file_obj: BinaryIO, buffer_size: int = BUFFER_BYTE_SIZE) -> None:
        super().__init__(file_obj, buffer_size)

    def write(self, bits: int | str) -> None:
        self._write_to_buffer(bits)

        if self.buffered_size < self.bit_buffer_size:
            return

        while self.buffered_size > self.bit_buffer_size:
            retval = self._read_from_buffer(self.bit_buffer_size)
            bytes_to_output = self._convert_to_bytes(retval)
            self.source_obj.write(bytes_to_output)

    @abc.abstractmethod
    def _convert_to_bytes(self) -> bytes:
        ...

    def flush(self) -> None:
        while self.buffered_size > 0:
            retval = self._read_from_buffer(self.bit_buffer_size)
            size = len(retval)
            if size < self.bit_buffer_size:
                self.byte_buffer_size = -(-size // 8)
                self.bit_buffer_size = self.byte_buffer_size * 8
                retval = retval.ljust(self.bit_buffer_size, "0")

            bytes_to_output = self._convert_to_bytes(retval)
            self.source_obj.write(bytes_to_output)

        self.buffered_bits = None
        self._flushed = True


def BufferedBitOutput(
    file_obj: BinaryIO, buffer_size: int = BUFFER_BYTE_SIZE, as_int: bool = False
) -> Union["BufferedIntegerOutput", "BufferedStringOutput"]:
    if isinstance(file_obj, (BufferedIntegerOutput, BufferedStringOutput)):
        return file_obj

    cls = BufferedStringOutput if not as_int else BufferedIntegerOutput

    return cls(file_obj, buffer_size)


class BufferedStringOutput(IBufferedStringIO, IBufferedBitOutput):
    def __init__(self, file_obj: BinaryIO, buffer_size: int = BUFFER_BYTE_SIZE) -> None:
        super().__init__(file_obj, buffer_size)


class BufferedIntegerOutput(IBufferedIntegerIO, IBufferedBitOutput):
    def __init__(self, file_obj: BinaryIO, buffer_size: int = BUFFER_BYTE_SIZE) -> None:
        super().__init__(file_obj, buffer_size)
