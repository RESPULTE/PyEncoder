from typing import BinaryIO, Union, Literal, Iterable

from pyencoder.utils.BitIO.mixin import MixinBufferedIntegerIO, MixinBufferedStringIO
from pyencoder.utils.BitIO.abc import IBufferedBitInput
from pyencoder.utils.BitIO import BUFFER_BITSIZE


def BufferedBitInput(
    source_obj: BinaryIO, buffer_size: int = BUFFER_BITSIZE, as_int: bool = False, default_value: str | int = None
) -> Union["BufferedIntegerInput", "BufferedStringInput"]:
    if isinstance(source_obj, (BufferedIntegerInput, BufferedStringInput)):
        return source_obj

    cls = BufferedStringInput if not as_int else BufferedIntegerInput
    return cls(source_obj, buffer_size, default_value)


class BufferedStringInput(MixinBufferedStringIO, IBufferedBitInput):
    def __init__(self, source_obj: BinaryIO, buffer_size: int = BUFFER_BITSIZE, default_value: str = None) -> None:
        super().__init__(source_obj, buffer_size)
        self.default_value = default_value

    def __iter__(self) -> Iterable[Literal["0", "1"]]:
        # python automatically converts bytes into a sequence of 8 bit integer when it is iterated
        for b in self.source_obj.read():
            bits = "{0:08b}".format(b)
            for i in range(0, 8):
                yield bits[i]


class BufferedIntegerInput(MixinBufferedIntegerIO, IBufferedBitInput):
    def __init__(self, source_obj: BinaryIO, buffer_size: int = BUFFER_BITSIZE, default_value: int = None) -> None:
        super().__init__(source_obj, buffer_size)
        self.default_value = default_value

    def __iter__(self) -> Iterable[Literal[0, 1]]:
        # python automatically converts bytes into a sequence of 8 bit integer when it is iterated
        for b in self.source_obj.read():
            for i in range(1, 9):
                yield (b >> (8 - i)) & 1
