import abc
import itertools
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
    def __init__(self, data: bytes | str = None) -> None:
        self._size = 0
        self._queue = None
        self._flushed = False

        if not data:
            return

        self.write(data)

    def _convert(self, data: bytes | str) -> Tuple[int, int]:
        if isinstance(data, str):
            return self.iterate_str_as_int(data), len(data)
        elif isinstance(data, bytes):
            return self._iterate_bytes_as_int(data), len(data) * 8

        raise TypeError("invalid type: {0}".format(type(data).__name__))

    def write(self, data: bytes | str) -> None:
        _iterator, size = self._convert(data)
        self._size += size
        self._flushed = False

        if self._queue != None:
            self._queue = itertools.chain(self._queue, _iterator)
            return
        self._queue = _iterator

    def read(self, n: int = None) -> None | int:
        if not self._flushed and self._size != 0:
            if n is None or n >= self._size:
                self._flushed = True
                n = self._size

            if n == 1:
                self._size -= 1
                return next(self._queue)

            i = 0
            buffer = 0
            while i < n:
                buffer = (buffer << 1) + next(self._queue)
                i += 1

            self._size -= n
            return buffer

        return None

    @staticmethod
    def _iterate_bytes_as_int(__bytes: bytes) -> Iterable[int]:
        for b in __bytes:
            for i in range(7, -1, -1):
                yield (b >> i) & 1

    @staticmethod
    def iterate_str_as_int(bits: str) -> Iterable[int]:
        for i in bits:
            yield int(i)

    def __bool__(self) -> bool:
        return self._size > 0

    def __len__(self) -> int:
        return self._size


class BitStringBuffer(BitBuffer):
    def __init__(self, data: bytes | str = None) -> None:
        self._queue = ""
        self._index = 0
        self._size = 0
        if not data:
            return

        self.write(data)

    def _convert(self, data: bytes | str) -> str:
        if isinstance(data, str):
            return data

        elif isinstance(data, bytes):
            return "".join(f"{x:08b}" for x in data)

        raise TypeError("invalid type: {0}".format(type(data).__name__))

    def write(self, data: bytes | str) -> None:
        data = self._convert(data)
        self._queue = self._queue[self._index :] + data

        self._size += len(data) - self._index
        self._index = 0

    def read(self, n: int = None) -> str:
        if self._queue:
            if n is None:
                retval = self._queue[self._index :]
                self._queue = ""
                self._index = 0
                self._size = 0
                return retval

            old_index = self._index
            self._index += n

            return self._queue[old_index : self._index]

        return None

    def __bool__(self) -> bool:
        return self._index < self._size

    def __len__(self) -> int:
        return self._size - self._index
