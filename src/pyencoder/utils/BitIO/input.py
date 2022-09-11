from typing import BinaryIO, Literal, Iterable

from pyencoder.utils.BitIO.mixin import MixinBufferedIntegerIO, MixinBufferedStringIO, MixinBufferedBitInput
from pyencoder.utils.BitIO import BUFFER_BITSIZE


class BufferedStringInput(MixinBufferedStringIO, MixinBufferedBitInput):
    def __init__(self, file_obj: BinaryIO, buffer_size: int = BUFFER_BITSIZE) -> None:
        super().__init__(file_obj, buffer_size)

    def __iter__(self) -> Iterable[Literal["0", "1"]]:
        # python automatically converts bytes into a sequence of 8 bit integer when it is iterated
        for b in self.file_obj.read():
            bits = "{0:08b}".format(b)
            for i in range(0, 8):
                yield bits[i]


class BufferedIntegerInput(MixinBufferedIntegerIO, MixinBufferedBitInput):
    def __init__(self, file_obj: BinaryIO, buffer_size: int = BUFFER_BITSIZE) -> None:
        super().__init__(file_obj, buffer_size)

    def __iter__(self) -> Iterable[Literal[0, 1]]:
        # python automatically converts bytes into a sequence of 8 bit integer when it is iterated
        for b in self.file_obj.read():
            for i in range(1, 9):
                yield (b >> (8 - i)) & 1
