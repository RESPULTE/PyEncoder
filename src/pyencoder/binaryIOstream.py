from abc import ABC, abstractmethod
from typing import BinaryIO, Literal


class BufferedBitStream(ABC):
    def __init__(self, filename: str) -> None:
        self.filename = filename
        self.cur_byte = bytes(0)
        self.num_bits = 0
        self.io: BinaryIO = None

    @abstractmethod
    def process(self) -> None:
        pass

    def __enter__(self):
        pass

    def __exit__(self, exc_type, exc_value, exc_traceback):
        self.io.close()


class BufferedBitReader(BufferedBitStream):
    def __init__(self, filename: str) -> None:
        super().__init__(filename)

    def process(self) -> int:
        if self.num_bits == 0:
            self.read_byte()

        self.num_bits -= 1
        return (self.cur_byte >> self.num_bits) & 1

    def read_byte(self) -> None:
        temp = self.io.read(1)
        self.cur_byte = temp[0]
        self.num_bits = 8

    def __enter__(self):
        self.file = open(self.filename, "rb")
        return self


class BufferedBitWriter(BufferedBitStream):
    def __init__(self, filename: str) -> None:
        super().__init__(filename)

    def process(self, bit: Literal[0] | Literal[1]) -> None:
        self.cur_byte = (self.cur_byte << 1) | bit
        self.num_bits += 1

        if self.num_bits == 8:
            self.write_byte()

    def write_byte(self) -> None:
        self.io.write((self.cur_byte,))
        self.cur_byte = bytes(0)
        self.num_bits = 8

    def __enter__(self):
        self.file = open(self.filename, "wb")
        return self
