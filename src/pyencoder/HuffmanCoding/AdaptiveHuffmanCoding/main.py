import io
from typing import Iterable, Generator

from pyencoder import Settings
from pyencoder.utils.BitIO.input import BufferedBitInput, BufferedStringInput

from pyencoder.HuffmanCoding.AdaptiveHuffmanCoding.codebook import AdaptiveHuffmanTree, get_huffman_code


class AdaptiveEncoder(AdaptiveHuffmanTree):
    def __init__(self) -> None:
        super().__init__()
        self.reset()

    def encode(self, symbol: str) -> str:
        return self._iterable.send(symbol)

    def flush(self) -> str:
        retval = self._iterable.send(Settings.EOF_MARKER)
        return retval

    def _encode(self) -> Generator[str, str, None]:
        huffman_code = ""
        try:
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

                self.update(node)

        except Exception as err:
            raise Exception("error occured while encoding") from err

    def reset(self) -> None:
        super().reset()

        self._iterable = self._encode()
        self._iterable.send(None)


class AdaptiveDecoder(AdaptiveHuffmanTree):
    def __init__(self) -> None:
        super().__init__()

    def decode(self, bitstream: str | bytes | io.BufferedReader) -> Iterable[str]:
        symbol_getter = self.get_symbol(BufferedBitInput(bitstream))
        while True:

            symbol = next(symbol_getter)
            if symbol is Settings.EOF_MARKER:
                break

            if symbol in self.symbol_catalogue:
                node = self.symbol_catalogue[symbol]

            else:
                node = self.create_node(symbol)
                if node.parent and not node.parent.is_root:
                    node = self.pre_process(node)

            self.update(node)

            yield symbol

    def get_symbol(self, bitstream: BufferedStringInput) -> Iterable[str]:
        yield Settings.FIXED_SYMBOL_LOOKUP[bitstream.read(Settings.FIXED_CODE_SIZE)]

        current_node = self.root
        while True:

            new_bit = bitstream.read(1)
            if new_bit == "0":
                current_node = current_node.left
            elif new_bit == "1":
                current_node = current_node.right
            else:
                raise ValueError(f"invalid bit found: {new_bit}")

            if current_node is self.NYT:
                symbol = Settings.FIXED_SYMBOL_LOOKUP[bitstream.read(Settings.FIXED_CODE_SIZE)]
                current_node = self.root
                yield symbol

            elif current_node.is_leaf:
                symbol = current_node.symbol
                current_node = self.root
                yield symbol
