from io import BufferedReader, BufferedWriter
from typing import Iterable, Literal

from pyencoder.type_hints import Bitcode
from pyencoder.config import ENDIAN


BUFFER_BYTE_SIZE = 1
BUFFER_BIT_SIZE = BUFFER_BYTE_SIZE * 8


class BufferedBitInput:
    def __init__(self, file_obj: BufferedWriter) -> None:
        self.file_obj = file_obj

        self.buffered_bits = ""
        self.buffered_size = 0

    def write(self, bits: Bitcode) -> None:
        self.buffered_bits += bits
        self.buffered_size += len(bits)

        if self.buffered_size < BUFFER_BIT_SIZE:
            return

        self.buffered_bits, bits_to_output = self.buffered_bits[BUFFER_BIT_SIZE:], self.buffered_bits[:BUFFER_BIT_SIZE]
        self.buffered_size -= BUFFER_BIT_SIZE

        bytes_to_output = int.to_bytes(int(bits_to_output, 2), BUFFER_BYTE_SIZE, ENDIAN)
        self.file_obj.write(bytes_to_output)

    def flush(self) -> None:
        if self.buffered_size == 0:
            return

        elif self.buffered_size < BUFFER_BIT_SIZE:
            self.buffered_bits = self.buffered_bits[::-1]

        bytes_to_output = int.to_bytes(int(self.buffered_bits, 2), BUFFER_BYTE_SIZE, ENDIAN)
        self.file_obj.write(bytes_to_output)

        self.buffered_bits = ""
        self.buffered_size = 0


class BufferedBitOutput:
    def __init__(self, file_obj: BufferedReader) -> None:
        self.file_obj = file_obj

        self.buffered_bits = ""
        self.buffered_index = 0

        self.finish = False

    def read(self, n: int) -> Bitcode:
        if self.finish:
            return ""

        new_buffered_index = self.buffered_index + n
        if new_buffered_index < BUFFER_BIT_SIZE and self.buffered_bits:
            retval = self.buffered_bits[self.buffered_index : new_buffered_index]
            self.buffered_index = new_buffered_index
            return retval

        buffered_bytes = self.file_obj.read(BUFFER_BYTE_SIZE)
        if not buffered_bytes:
            return self.flush()

        new_buffered_bits = "{:08b}".format(int(buffered_bytes.hex(), 16))
        if self.buffered_index == BUFFER_BIT_SIZE or not self.buffered_bits:
            new_buffered_index = n
            retval = new_buffered_bits[:n]

        else:
            new_buffered_index = new_buffered_index - BUFFER_BIT_SIZE
            retval = self.buffered_bits[self.buffered_index :] + new_buffered_bits[:new_buffered_index]

        self.buffered_index = new_buffered_index
        self.buffered_bits = new_buffered_bits

        return retval

    def flush(self) -> Bitcode:
        self.finish = True
        return self.buffered_bits[self.buffered_index :]

    def __iter__(self) -> Iterable[Literal["0", "1"]]:
        # python automatically converts bytes into a sequence of 8 bit integer when it is iterated
        for b in self.file_obj.read():
            for i in range(1, 9):
                yield (b >> (8 - i)) & 1
