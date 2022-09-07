from typing import TypeVar


__T = TypeVar("__T")


class DecodingError(Exception):
    pass


class EncodingError(Exception):
    pass


class CorruptedHeaderError(Exception):
    pass


class CorruptedEncodingError(Exception):
    pass
