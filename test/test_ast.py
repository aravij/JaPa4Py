from unittest import TestCase
from pathlib import Path
from typing import Dict, Set

from src import AST, ASTNodeType, NodesSearchFilter


class ASTTestSuite(TestCase):
    def test_parsing(self):
        ast = AST.build(self._current_dir / "SimpleClass.java")
        actual_node_types = [node.node_type for node in ast.nodes]
        self.assertEqual(actual_node_types, ASTTestSuite._simple_class_preordered)

    def test_finding_nodes(self):
        ast = AST.build(self._current_dir / "AnonymousClass.java")
        for filter_type in NodesSearchFilter:
            found_methods = ast.find_nodes(ASTNodeType.METHOD_DECLARATION, search_filter=filter_type)
            method_names = {method.name for method in found_methods}
            self.assertEqual(
                method_names,
                self._anonymous_class_method_names[filter_type],
                f"Failed finding nodes with filter {filter_type}.",
            )

    def test_complex_fields(self):
        ast = AST.build(self._current_dir / "StaticConstructor.java")
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

    _current_dir = Path(__file__).parent.absolute()

    _simple_class_preordered = [
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

    _anonymous_class_method_names: Dict[NodesSearchFilter, Set[str]] = {
        NodesSearchFilter.ALL: {"method", "overriddenMethod1", "overriddenMethod2"},
        NodesSearchFilter.TOP_LEVEL: {"method"},
        NodesSearchFilter.BOTTOM_LEVEL: {"overriddenMethod1", "overriddenMethod2"},
    }
