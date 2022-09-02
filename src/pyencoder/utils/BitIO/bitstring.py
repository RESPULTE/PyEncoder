from typing import Dict, Type, TypeVar


class UnsignedBitstring:
    def __new__(cls, data: str, _cache: Dict[str, "UnsignedBitstring"] = {}) -> None:
        if not isinstance(data, str):
            raise TypeError(f"invalid type: {type(data).__name__}")

        elif not all(x in ("0", "1") for x in data):
            raise ValueError(f"bits must only contain 1s and 0s")

        if data in _cache:
            return _cache[data]

        elif isinstance(data, cls):
            return data

        obj = super().__new__(cls)
        _cache[data] = obj
        return obj

    def __init__(self, data: str) -> None:
        self.data = data

    def __invert__(self) -> "UnsignedBitstring":
        return type(self)(self.data)

    def __int__(self) -> int:
        return int(self.data, 2)

    def concatenate(self, other: "UnsignedBitstring") -> "UnsignedBitstring":
        return type(self)(self.data + other.data)
