import abc
import collections
from typing import Iterable, Tuple
from pyencoder import Settings


class BitBuffer(abc.ABC):
    @abc.abstractmethod
    def _convert(self, data):
        ...

    @abc.abstractmethod
    def write(self, data):
        ...

    @abc.abstractmethod
    def read(self):
        ...

    @abc.abstractmethod
    def __bool__(self):
        ...

    @abc.abstractmethod
    def __len__(self):
        ...


class BitIntegerBuffer(BitBuffer):
    def __init__(self, data: bytes | str | int = None) -> None:
        self._queue = collections.deque([])
        if not data:
            return

        self.write(data)

    def _convert(self, data: bytes | str | int) -> Tuple[int, int]:
        if isinstance(data, str):
            as_int = int(data, 2)
            size = len(data)
        elif isinstance(data, bytes):
            as_int = int.from_bytes(data, Settings.ENDIAN)
            size = len(data) * 8
        elif isinstance(data, int):
            as_int = data
            size = data.bit_length()
        else:
            raise TypeError("invalid type: {0}".format(type(data).__name__))

        return as_int, size

    def write(self, data: bytes | str | int) -> None:
        self._queue.extend(self._iterate(*self._convert(data)))

    def read(self, n: int = None) -> None | int:
        if self._queue:
            if n is None:
                n = len(self._queue)

            i = 0
            buffer = 0
            while i < n:
                buffer = (buffer << 1) + self._queue.popleft()
                i += 1
            return buffer

        return None

    @staticmethod
    def _iterate(__ints: int, __size: int) -> Iterable[int]:
        for i in range(__size - 1, -1, -1):
            yield (__ints >> i) & 1

    def __bool__(self) -> bool:
        return not not self._queue

    def __len__(self) -> int:
        return len(self._queue)


class BitStringBuffer(BitBuffer):
    def __init__(self, data: bytes | str | int = None) -> None:
        self._queue = ""
        if not data:
            return

        self.write(data)

    def _convert(self, data: bytes | str | int) -> str:
        if isinstance(data, str):
            as_str = data

        elif isinstance(data, bytes):
            as_str = "{0:0{size}b}".format(int.from_bytes(data, Settings.ENDIAN), size=len(data) * 8)

        elif isinstance(data, int):
            as_str = "{0:b}".format(data)

        else:
            raise TypeError("invalid type: {0}".format(type(data).__name__))

        return as_str

    def write(self, data: bytes | str | int) -> None:
        self._queue += self._convert(data)

    def read(self, n: int = None) -> str | None:
        if self._queue:
            if n is None:
                retval = "".join(self._queue)
                self._queue = ""
                return retval

            retval = self._queue[:n]
            self._queue = self._queue[n:]

            return retval

        return None

    def __bool__(self) -> bool:
        return not not self._queue

    def __len__(self) -> int:
        return len(self._queue)
