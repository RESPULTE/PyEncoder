from typing import Iterable, Literal, BinaryIO, Union

from pyencoder.utils.BitIO.abc import *

BUFFER_BYTE_SIZE = 1


def BufferedBitInput(
    file_obj: BinaryIO, buffer_size: int = BUFFER_BYTE_SIZE, as_int: bool = False
) -> Union["BufferedBitIntegerInput", "BufferedStringInput"]:
    cls = BufferedStringInput if not as_int else BufferedBitIntegerInput
    return cls(file_obj, buffer_size)


def BufferedBitOutput(
    file_obj: BinaryIO, buffer_size: int = BUFFER_BYTE_SIZE, as_int: bool = False
) -> Union["BufferedIntegerOutput", "BufferedStringOutput"]:
    cls = BufferedStringOutput if not as_int else BufferedIntegerOutput
    return cls(file_obj, buffer_size)


class BufferedStringInput(BufferedStringIO, BufferedInput):
    def __init__(self, file_obj: BinaryIO, buffer_size: int = BUFFER_BYTE_SIZE) -> None:
        super().__init__(file_obj, buffer_size)

    def __iter__(self) -> Iterable[Literal["0", "1"]]:
        # python automatically converts bytes into a sequence of 8 bit integer when it is iterated
        for b in self.file_obj.read():
            bits = "{0:08b}".format(b)
            for i in range(0, 8):
                yield bits[i]


class BufferedBitIntegerInput(BufferedIntegerIO, BufferedInput):
    def __init__(self, file_obj: BinaryIO, buffer_size: int = BUFFER_BYTE_SIZE) -> None:
        super().__init__(file_obj, buffer_size)

    def __iter__(self) -> Iterable[Literal[0, 1]]:
        # python automatically converts bytes into a sequence of 8 bit integer when it is iterated
        for b in self.file_obj.read():
            for i in range(1, 9):
                yield (b >> (8 - i)) & 1


class BufferedStringOutput(BufferedStringIO, BufferedOutput):
    def __init__(self, file_obj: BinaryIO, buffer_size: int = BUFFER_BYTE_SIZE) -> None:
        super().__init__(file_obj, buffer_size)


class BufferedIntegerOutput(BufferedIntegerIO, BufferedOutput):
    def __init__(self, file_obj: BinaryIO, buffer_size: int = BUFFER_BYTE_SIZE) -> None:
        super().__init__(file_obj, buffer_size)
