from typing import Dict, Iterable, Tuple, Union

from pyencoder import Settings


class SingletonBitType(type):
    __cache: Dict[Tuple[int, int], object] = {}

    def __call__(cls, data: bytes | str | int, size: int = None):
        (data, size) = cls._convert(data, size)
        if (data, size) not in cls.__cache:
            cls.__cache[(data, size)] = super(SingletonBitType, cls).__call__(data, size)

        return cls.__cache[(data, size)]


class BitInteger(int, metaclass=SingletonBitType):
    def __new__(cls, data: bytes | str | int, size: int = None) -> None:
        return super().__new__(cls, data)

    def __init__(self, data: bytes | str | int, size: int = None) -> None:
        super().__init__()
        self.size = size

    def lslice(self, n: int) -> Tuple["BitInteger", "BitInteger"]:
        index = self.size - n

        left_slicer = (1 << n) - 1
        right_slicer = (1 << index) - 1

        retval_left_slice = (self & (left_slicer << index)) >> index
        retval_right_slice = self & right_slicer

        return retval_left_slice, retval_right_slice

    @staticmethod
    def _convert(data: bytes | str | int, size: int = None) -> Tuple[int, int]:
        if isinstance(data, bytes):
            size = size or len(data) * 8
            data = int.from_bytes(data, Settings.ENDIAN)

        elif isinstance(data, str):
            size = size or len(data)
            data = int(data, 2)

        elif isinstance(data, int):
            size = size or data.bit_length()
            data = data

        else:
            raise TypeError(f"invalid type for bitstring: {type(data).__name__}")

        if size < data.bit_length():
            raise ValueError(f"size ({size}) is too smaller than data's size ({data.bit_length()})")

        return data, size

    def __lshift__(self, other: Union[int, "BitInteger"]) -> "BitInteger":
        return type(self)(super().__lshift__(other), self.size + other)

    def __rshift__(self, other: Union[int, "BitInteger"]) -> "BitInteger":
        return type(self)(super().__rshift__(other), max(0, self.size - other))

    def __and__(self, other: Union[int, "BitInteger"]) -> "BitInteger":
        return type(self)(super().__and__(other), min(self.size, other.bit_length()))

    def __or__(self, other: Union[int, "BitInteger"]) -> "BitInteger":
        return type(self)(super().__or__(other), max(self.size, other.bit_length()))

    def __rlshift__(self, other: Union[int, "BitInteger"]) -> int:
        return other << self.size

    def __rrshift__(self, other: Union[int, "BitInteger"]) -> int:
        return other >> self.size

    def __invert__(self) -> "BitInteger":
        raise NotImplementedError

    def __str__(self) -> str:
        return f"{self.__class__.__name__}({format(self, f'0{self.size}b')})"

    def __len__(self) -> int:
        return self.size

    def __iter__(self) -> Iterable:
        for i in range(self.size - 1, -1, -1):
            yield (self >> i) & 1

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(self={format(self, f'0{self.size}b')}, data={self}, size={self.size})"
