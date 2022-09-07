from typing import Dict, Iterable, Literal, Type, TypeVar

from pyencoder import Config

# take in bytes
# spits out an Iterable of choosing (str/int)
class Bitstring(str):
    _cache: Dict[str, "Bitstring"] = {}

    def __new__(cls, data: bytes, *arg, **kwarg) -> None:
        if data in cls._cache:
            return cls._cache[data]

        obj = super().__new__(cls)
        cls._cache[data] = obj
        return obj

    def __init__(self, data: bytes, retval: Type[str] | Type[int]) -> None:
        try:
            self.data = int.from_bytes(data, Config["ENDIAN"])
        except TypeError as err:
            raise TypeError(f"invalid type for bitstring: {type(data)}") from err

        self.size = len(data) * 8
        self.retval = retval

        if retval is str:
            self.data = "{0:0{bit_len}b}".format(self.data, bit_len=self.size)

    def __iter__(self) -> Iterable:
        if self.retval is str:
            yield from self.data
            return

        for i in range(self.size - 1, -1, -1):
            yield (self.data >> i) & 1

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(data={self.data}, size={self.size}, retval={self.retval.__name__})"


class BitInteger(int):
    ...
