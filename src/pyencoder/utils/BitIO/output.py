from typing import BinaryIO

from pyencoder.utils.BitIO.mixin import MixinBufferedIntegerIO, MixinBufferedStringIO, MixinBufferedBitOutput
from pyencoder.utils.BitIO import BUFFER_BITSIZE


class BufferedStringOutput(MixinBufferedStringIO, MixinBufferedBitOutput):
    def __init__(self, file_obj: BinaryIO, buffer_size: int = BUFFER_BITSIZE) -> None:
        super().__init__(file_obj, buffer_size)


class BufferedIntegerOutput(MixinBufferedIntegerIO, MixinBufferedBitOutput):
    def __init__(self, file_obj: BinaryIO, buffer_size: int = BUFFER_BITSIZE) -> None:
        super().__init__(file_obj, buffer_size)
