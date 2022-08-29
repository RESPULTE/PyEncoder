import abc
from typing import BinaryIO

from pyencoder.config import ENDIAN

from pyencoder.utils.binary import left_shift, right_shift

BUFFER_BYTE_SIZE = 1


class BufferedIO(abc.ABC):
    def __init__(self, file_obj: BinaryIO, buffer_size: int = BUFFER_BYTE_SIZE) -> None:
        self.file_obj = file_obj

        self.byte_buffer_size = buffer_size
        self.bit_buffer_size = buffer_size * 8

        self.buffered_size = 0
        self.buffered_bits = None

        self._flushed = False

    @abc.abstractmethod
    def read_from_buffer(self, n: int) -> int | str:
        ...

    @abc.abstractmethod
    def write_to_buffer(self, bits: int | str) -> None:
        ...

    @abc.abstractmethod
    def flush(self) -> int | str:
        ...


class BufferedInput(BufferedIO):
    def __init__(self, file_obj: BinaryIO, buffer_size: int = BUFFER_BYTE_SIZE) -> None:
        super().__init__(file_obj, buffer_size)

    def read(self, n: int) -> int | str:
        # if reading process is finished
        if self._flushed or n <= 0:
            return None

        # if the bits left in the buffer is more than the requested amount
        if n < self.buffered_size:
            return self.read_from_buffer(n)

        buffered_bytes = self.file_obj.read(self.byte_buffer_size)

        # if the file has been exhausted
        if not buffered_bytes:
            return self.flush()

        new_buffered_bits = self._convert_from_bytes(buffered_bytes)

        # if the current buffer has been exhausted
        if not self.buffered_size:
            self.buffered_bits = new_buffered_bits
            self.buffered_size = self.bit_buffer_size

        # if the current buffer still hasn't been exhausted
        else:
            self.write_to_buffer(new_buffered_bits)

        return self.read_from_buffer(n)

    def flush(self) -> str:
        retval = self.buffered_bits
        self.buffered_index = 0
        self.buffered_bits = None
        self._flushed = True
        return retval

    @abc.abstractmethod
    def _convert_from_bytes(self, _bytes: bytes) -> str | int:
        ...


class BufferedOutput(BufferedIO):
    def __init__(self, file_obj: BinaryIO, buffer_size: int = BUFFER_BYTE_SIZE) -> None:
        super().__init__(file_obj, buffer_size)

    def write(self, bits: int | str) -> None:
        self.write_to_buffer(bits)

        if self.buffered_size < self.bit_buffer_size:
            return

        retval = self.read_from_buffer(self.bit_buffer_size)
        bytes_to_output = self._convert_to_bytes(retval)
        self.file_obj.write(bytes_to_output)

    @abc.abstractmethod
    def _convert_to_bytes(self) -> bytes:
        ...

    def flush(self) -> None:
        if self.buffered_size != 0:
            bytes_to_output = self._convert_to_bytes(self.buffered_bits)
            self.file_obj.write(bytes_to_output)

        self.buffered_size = 0
        self.buffered_bits = None


class BufferedIntegerIO(BufferedIO):
    def __init__(self, file_obj: BinaryIO, buffer_size: int = BUFFER_BYTE_SIZE) -> None:
        super().__init__(file_obj, buffer_size)
        self.buffered_bits = 0

    def read_from_buffer(self, n: int) -> int:
        retval = left_shift(self.buffered_bits, 0, n)
        self.buffered_bits = right_shift(self.buffered_bits, 0, self.buffered_size - n)
        self.buffered_size -= n
        return retval

    def write_to_buffer(self, bits: int) -> None:
        bit_size = bits.bit_length()
        self.buffered_bits = (self.buffered_bits << bit_size) | bits
        self.buffered_size += bit_size

    def _convert_to_bytes(self, bits: int) -> bytes:
        return int.to_bytes(bits, self.byte_buffer_size, ENDIAN)

    def _convert_from_bytes(self, _bytes: bytes) -> int:
        return int.from_bytes(_bytes, ENDIAN)


class BufferedStringIO(BufferedIO):
    def __init__(self, file_obj: BinaryIO, buffer_size: int = BUFFER_BYTE_SIZE) -> None:
        super().__init__(file_obj, buffer_size)
        self.buffered_bits = ""

    def read_from_buffer(self, n: int) -> str:
        self.buffered_size -= n
        retval = self.buffered_bits[:n]
        self.buffered_bits = self.buffered_bits[n:]
        return retval

    def write_to_buffer(self, bits: str) -> None:
        self.buffered_bits += bits
        self.buffered_size += len(bits)

    def _convert_to_bytes(self, bits: str) -> bytes:
        return int.to_bytes(int(bits, 2), self.byte_buffer_size, ENDIAN)

    def _convert_from_bytes(self, _bytes: bytes) -> str:
        return "{0:08b}".format(int.from_bytes(_bytes, ENDIAN))
