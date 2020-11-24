from typing import Union, TYPE_CHECKING

from javalang.parse import parse

from .encoding_detector import read_text_with_autodetected_encoding

if TYPE_CHECKING:
    from pathlib import Path
    from javalang.tree import CompilationUnit


def build_ast(filename: Union[str, "Path"]) -> "CompilationUnit":
    return parse(read_text_with_autodetected_encoding(str(filename)))
