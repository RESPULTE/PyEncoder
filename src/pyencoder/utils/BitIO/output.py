from typing import BinaryIO, Union

from pyencoder.utils.BitIO.mixin import MixinBufferedIntegerIO, MixinBufferedStringIO
from pyencoder.utils.BitIO.abc import IBufferedBitOutput
from pyencoder.utils.BitIO import BUFFER_BITSIZE


def BufferedBitOutput(
    file_obj: BinaryIO, buffer_size: int = BUFFER_BITSIZE, as_int: bool = False
) -> Union["BufferedIntegerOutput", "BufferedStringOutput"]:
    if isinstance(file_obj, (BufferedIntegerOutput, BufferedStringOutput)):
        return file_obj

    cls = BufferedStringOutput if not as_int else BufferedIntegerOutput

    return cls(file_obj, buffer_size)


class BufferedStringOutput(MixinBufferedStringIO, IBufferedBitOutput):
    def __init__(self, file_obj: BinaryIO, buffer_size: int = BUFFER_BITSIZE) -> None:
        super().__init__(file_obj, buffer_size)


class BufferedIntegerOutput(MixinBufferedIntegerIO, IBufferedBitOutput):
    def __init__(self, file_obj: BinaryIO, buffer_size: int = BUFFER_BITSIZE) -> None:
        super().__init__(file_obj, buffer_size)
