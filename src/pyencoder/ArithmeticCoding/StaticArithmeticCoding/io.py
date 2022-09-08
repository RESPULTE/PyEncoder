from typing import BinaryIO, Dict, TextIO

from pyencoder.utils.BitIO.input import BufferedStringInput


def load(input_file: BinaryIO, output_file: TextIO | None) -> None | str:
    ...


def dump(input_file: TextIO | str, output_file: BinaryIO) -> None:
    ...


def generate_header_from_codebook(codebook: Dict[str, int]) -> str:
    ...


def generate_codebook_from_header(bitstream: BufferedStringInput) -> Dict[str, int]:
    ...
