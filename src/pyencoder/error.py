class CorruptedHeaderError(Exception):
    pass


class CorruptedEncodingError(Exception):
    pass


class UnknownSymbolError(Exception):
    def __init__(self, unknown_symbol: str) -> None:
        super().__init__("unknown symbol found: {0}".format(unknown_symbol))
