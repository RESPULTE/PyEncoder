from typing import Generator

from pyencoder import Settings
from pyencoder.utils.bitbuffer import BitStringBuffer

from pyencoder.HuffmanCoding.AdaptiveHuffmanCoding.codebook import AdaptiveHuffmanTree, get_huffman_code


class AdaptiveEncoder(AdaptiveHuffmanTree):
    def __init__(self) -> None:
        super().__init__()

        self._encoder = self._encode()
        self._encoder.send(None)

    def encode(self, symbol: str) -> str:
        if symbol not in Settings.SYMBOLS:
            raise ValueError(f"Unknown Symbol Found: {symbol}")

        return self._encoder.send(symbol)

    def flush(self) -> str:
        retval = self._encoder.send(Settings.EOF_MARKER)
        self._encoder.close()
        self.reset()
        return retval

    def _encode(self) -> Generator[str, str, None]:
        huffman_code = ""

        while True:
            symbol = yield huffman_code
            if symbol in self.symbol_catalogue:
                node = self.symbol_catalogue[symbol]
                huffman_code = get_huffman_code(node)

            else:
                huffman_code = get_huffman_code(self.NYT) + Settings.FIXED_CODE_LOOKUP[symbol]

                node = self.create_node(symbol)
                if node.parent and not node.parent.is_root:
                    node = self.pre_process(node)

            self._update_node_relation(node)

    def reset(self) -> None:
        self.__init__()


class AdaptiveDecoder(AdaptiveHuffmanTree):
    def __init__(self) -> None:
        super().__init__()

        self.bitstream = BitStringBuffer()
        self._decoder = self._decode()
        self._decoder.send(None)

        self._primed = False

    def decode(self, bits: bytes | str | int) -> str:
        if not self._primed:
            self.bitstream.write(bits)
            if len(self.bitstream) < Settings.FIXED_CODE_SIZE:
                return ""

            code = self.bitstream.read(Settings.FIXED_CODE_SIZE)
            symbol = Settings.FIXED_SYMBOL_LOOKUP[code]
            if symbol == Settings.EOF_MARKER:
                return ""

            self._update(symbol)
            self._primed = True
            return symbol

        return self._decoder.send(bits)

    def _decode(self) -> Generator[str, str, None]:
        current_node = self.root
        decoded_symbols = ""

        while True:

            bits = yield decoded_symbols
            self.bitstream.write(bits)
            decoded_symbols = ""

            while self.bitstream:

                new_bit = self.bitstream.read(1)
                if new_bit == "0":
                    current_node = current_node.left
                elif new_bit == "1":
                    current_node = current_node.right
                else:
                    raise ValueError(f"invalid bit found: ({new_bit})")

                if current_node is self.NYT:
                    while len(self.bitstream) < Settings.FIXED_CODE_SIZE:
                        bits = yield ""
                        self.bitstream.write(bits)

                    code = self.bitstream.read(Settings.FIXED_CODE_SIZE)
                    new_symbol = Settings.FIXED_SYMBOL_LOOKUP[code]

                    if new_symbol == Settings.EOF_MARKER:
                        yield decoded_symbols
                        return

                    decoded_symbols += new_symbol
                    current_node = self.root
                    self._update(new_symbol)

                elif current_node.is_leaf:
                    new_symbol = current_node.symbol
                    decoded_symbols += new_symbol
                    current_node = self.root
                    self._update(new_symbol)

    def _update(self, symbol: str) -> None:
        if symbol in self.symbol_catalogue:
            node = self.symbol_catalogue[symbol]

        else:
            node = self.create_node(symbol)
            if node.parent and not node.parent.is_root:
                node = self.pre_process(node)

        self._update_node_relation(node)

    def flush(self) -> str:
        self.reset()
        return ""

    def reset(self) -> None:
        self.__init__()
