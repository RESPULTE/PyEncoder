import functools
from typing import BinaryIO

from pyencoder import Settings

from pyencoder.utils.BitIO.abc import IBufferedBitTypeIO, IBufferedBitOutput, IBufferedBitInput
from pyencoder.utils.BitIO import BUFFER_BITSIZE
from pyencoder.utils.bitbuffer import BitIntegerBuffer, BitStringBuffer


class MixinBufferedIntegerIO(IBufferedBitTypeIO):
    def __init__(self, file_obj: BinaryIO | bytes | str, buffer_size: int = BUFFER_BITSIZE) -> None:
        super().__init__(file_obj, buffer_size)
        self.buffer = BitIntegerBuffer()

    def _convert_to_bytes(self, data: int) -> bytes:
        return int.to_bytes(data, -(-data.bit_length() // 8), Settings.ENDIAN)


class MixinBufferedStringIO(IBufferedBitTypeIO):
    def __init__(self, file_obj: BinaryIO, buffer_size: int = BUFFER_BITSIZE) -> None:
        super().__init__(file_obj, buffer_size)
        self.buffer = BitStringBuffer()

    def _convert_to_bytes(self, data: str) -> bytes:
        _int = int(data, 2)
        return int.to_bytes(_int, -(-len(data) // 8), Settings.ENDIAN)


class MixinBufferedBitInput(IBufferedBitInput):
    def __init__(self, file_obj: BinaryIO, buffer_size: int = BUFFER_BITSIZE) -> None:
        super().__init__(file_obj, buffer_size)

        if not hasattr(self.file_obj, "read"):
            raise TypeError(f"invalid type {type(file_obj)}")

    def read(self, n: int = None) -> int | str:
        # if reading process is finished
        if self._flushed:
            return None

        if n is None:
            self.buffer.write(self.file_obj.read())
            return self.flush()

        # if the bits left in the buffer is more than the requested amount
        if n <= len(self.buffer):
            return self.buffer.read(n)

        while len(self.buffer) < n:
            source_data = self.file_obj.read(self.buffer_size // 8)

            if not source_data:
                return self.flush()

            self.buffer.write(source_data)

        return self.buffer.read(n)

    def flush(self) -> str:
        self._flushed = True
        return self.buffer.read()


class MixinBufferedBitOutput(IBufferedBitOutput):
    def __init__(self, file_obj: BinaryIO, buffer_size: int = BUFFER_BITSIZE) -> None:
        super().__init__(file_obj, buffer_size)

    def write(self, bits: int | str) -> None:
        self.buffer.write(bits)

        if len(self.buffer) < self.buffer_size:
            return

        while len(self.buffer) > self.buffer_size:
            retval = self.buffer.read(self.buffer_size)
            bytes_to_output = self._convert_to_bytes(retval)
            self.file_obj.write(bytes_to_output)

    def flush(self) -> None:
        self._resolve_incomplete_bytes()
        bytes_to_output = self._convert_to_bytes(self.buffer.read())
        self.file_obj.write(bytes_to_output)

        self.buffer = None
        self._flushed = True

    def _resolve_incomplete_bytes(self) -> None:
        size = 8 - len(self.buffer) % 8
        if size == 8:
            return
        self.buffer.write("0" * size)
