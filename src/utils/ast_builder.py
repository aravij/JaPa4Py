from typing import TYPE_CHECKING

from javalang.parse import parse

from .encoding_detector import read_text_with_autodetected_encoding

if TYPE_CHECKING:
    from javalang.tree import CompilationUnit


def build_ast(filename: str) -> "CompilationUnit":
    return parse(read_text_with_autodetected_encoding(filename))
