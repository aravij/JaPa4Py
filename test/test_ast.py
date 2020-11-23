from unittest import TestCase
from pathlib import Path
from itertools import zip_longest

from src.utils.ast_builder import build_ast
from src import AST, ASTNodeType


class ASTTestSuite(TestCase):
    def test_parsing(self):
        ast = self._build_ast("SimpleClass.java")
        actual_node_types = [node.node_type for node in ast]
        self.assertEqual(actual_node_types, ASTTestSuite._java_simple_class_preordered)

    def test_subtrees_selection(self):
        ast = self._build_ast("SimpleClass.java")
        subtrees = ast.get_subtrees(ASTNodeType.BASIC_TYPE)
        for actual_subtree, expected_subtree in zip_longest(
            subtrees, ASTTestSuite._java_simple_class_basic_type_subtrees
        ):
            with self.subTest():
                self.assertEqual([node.node_index for node in actual_subtree], expected_subtree)

    def test_complex_fields(self):
        ast = self._build_ast("StaticConstructor.java")
        class_declaration = next(
            (
                declaration
                for declaration in ast.get_root().types
                if declaration.node_type == ASTNodeType.CLASS_DECLARATION
            ),
            None,
        )
        assert class_declaration is not None, "Cannot find class declaration"

        static_constructor, method_declaration = class_declaration.body
        self.assertEqual(
            [node.node_type for node in static_constructor],
            [ASTNodeType.STATEMENT_EXPRESSION, ASTNodeType.STATEMENT_EXPRESSION],
        )
        self.assertEqual(method_declaration.node_type, ASTNodeType.METHOD_DECLARATION)

    def _build_ast(self, filename: str):
        javalang_ast = build_ast(str(Path(__file__).parent.absolute() / filename))
        return AST.build_from_javalang(javalang_ast)

    _java_simple_class_preordered = [
        ASTNodeType.COMPILATION_UNIT,
        ASTNodeType.CLASS_DECLARATION,
        ASTNodeType.COLLECTION,
        ASTNodeType.STRING,
        ASTNodeType.FIELD_DECLARATION,
        ASTNodeType.COLLECTION,
        ASTNodeType.STRING,
        ASTNodeType.BASIC_TYPE,
        ASTNodeType.STRING,
        ASTNodeType.VARIABLE_DECLARATOR,
        ASTNodeType.STRING,
        ASTNodeType.LITERAL,
        ASTNodeType.STRING,
        ASTNodeType.METHOD_DECLARATION,
        ASTNodeType.COLLECTION,
        ASTNodeType.STRING,
        ASTNodeType.BASIC_TYPE,
        ASTNodeType.STRING,
        ASTNodeType.STRING,
        ASTNodeType.STATEMENT_EXPRESSION,
        ASTNodeType.ASSIGNMENT,
        ASTNodeType.MEMBER_REFERENCE,
        ASTNodeType.STRING,
        ASTNodeType.STRING,
        ASTNodeType.LITERAL,
        ASTNodeType.STRING,
        ASTNodeType.STRING,
        ASTNodeType.RETURN_STATEMENT,
        ASTNodeType.MEMBER_REFERENCE,
        ASTNodeType.STRING,
        ASTNodeType.STRING,
    ]

    _java_simple_class_basic_type_subtrees = [
        [8, 9],
        [17, 18],
    ]
