from typing import Any, cast, Dict, List, Set, Tuple, Union, TYPE_CHECKING

from networkx import DiGraph  # type: ignore
from javalang.tree import Node
from javalang.parse import parse

from .ast_node_type import ASTNodeType
from ._auxiliary_data import attributes_by_node_type, javalang_to_ast_node_type, ASTNodeReference
from .utils.encoding_detector import read_text_with_autodetected_encoding

if TYPE_CHECKING:
    from pathlib import Path  # noqa: F401


class AstBuilder:
    def build(self, source_code_filepath: Union[str, "Path"]) -> Tuple[DiGraph, int]:
        self._create_initial_state()

        source_code = read_text_with_autodetected_encoding(str(source_code_filepath))
        javalang_ast = parse(source_code)

        root_id = self._add_subtree_from_javalang_node(javalang_ast)
        self._replace_javalang_nodes_in_attributes()

        return self._graph, root_id

    def _create_initial_state(self) -> None:
        self._graph: DiGraph = DiGraph()
        self._javalang_node_to_index_map: Dict[Node, int] = {}

    def _add_subtree_from_javalang_node(
        self,
        javalang_node: Union[Node, Set[Any], str],
    ) -> int:
        node_index, node_type = self._add_javalang_node(javalang_node)
        if node_index != self._UNKNOWN_NODE_TYPE and node_type not in {ASTNodeType.COLLECTION, ASTNodeType.STRING}:
            javalang_standard_node = cast(Node, javalang_node)
            self._javalang_node_to_index_map[javalang_standard_node] = node_index
            self._add_javalang_children(
                javalang_standard_node.children,
                node_index,
            )
        return node_index

    def _add_javalang_children(
        self,
        children: List[Any],
        parent_index: int,
    ) -> None:
        for child in children:
            if isinstance(child, list):
                self._add_javalang_children(child, parent_index)
            else:
                child_index = self._add_subtree_from_javalang_node(child)
                if child_index != self._UNKNOWN_NODE_TYPE:
                    self._graph.add_edge(parent_index, child_index)

    def _add_javalang_node(self, javalang_node: Union[Node, Set[Any], str]) -> Tuple[int, ASTNodeType]:
        node_index = self._UNKNOWN_NODE_TYPE
        node_type = ASTNodeType.UNKNOWN
        if isinstance(javalang_node, Node):
            node_index, node_type = self._add_javalang_standard_node(javalang_node)
        elif isinstance(javalang_node, set):
            node_index = self._add_javalang_collection_node(javalang_node)
            node_type = ASTNodeType.COLLECTION
        elif isinstance(javalang_node, str):
            node_index = self._add_javalang_string_node(javalang_node)
            node_type = ASTNodeType.STRING

        return node_index, node_type

    def _add_javalang_standard_node(self, javalang_node: Node) -> Tuple[int, ASTNodeType]:
        node_index = len(self._graph) + 1
        node_type = javalang_to_ast_node_type[type(javalang_node)]

        attr_names = attributes_by_node_type[node_type]
        attributes = {attr_name: getattr(javalang_node, attr_name) for attr_name in attr_names}

        attributes["node_type"] = node_type
        attributes["line"] = javalang_node.position.line if javalang_node.position is not None else None

        self._post_process_javalang_attributes(node_type, attributes)

        self._graph.add_node(node_index, **attributes)
        return node_index, node_type

    def _post_process_javalang_attributes(self, node_type: ASTNodeType, attributes: Dict[str, Any]) -> None:
        """
        Replace some attributes with more appropriate values for convenient work
        """

        if node_type == ASTNodeType.METHOD_DECLARATION and attributes["body"] is None:
            attributes["body"] = []

        if node_type == ASTNodeType.LAMBDA_EXPRESSION and isinstance(attributes["body"], Node):
            attributes["body"] = [attributes["body"]]

        if node_type in {ASTNodeType.METHOD_INVOCATION, ASTNodeType.MEMBER_REFERENCE} and attributes["qualifier"] == "":
            attributes["qualifier"] = None

    def _add_javalang_collection_node(self, collection_node: Set[Any]) -> int:
        node_index = len(self._graph) + 1
        self._graph.add_node(node_index, node_type=ASTNodeType.COLLECTION, line=None)
        # we expect only strings in collection
        # we add them here as children
        for item in collection_node:
            if type(item) == str:
                string_node_index = self._add_javalang_string_node(item)
                self._graph.add_edge(node_index, string_node_index)
            elif item is not None:
                raise ValueError(
                    'Unexpected javalang AST node type {} inside "COLLECTION" node'.format(type(item))
                )
        return node_index

    def _add_javalang_string_node(self, string_node: str) -> int:
        node_index = len(self._graph) + 1
        self._graph.add_node(node_index, node_type=ASTNodeType.STRING, string=string_node, line=None)
        return node_index

    def _replace_javalang_nodes_in_attributes(self) -> None:
        """
        All javalang nodes found in networkx nodes attributes are replaced
        with references to according networkx nodes.
        Supported attributes types:
         - single javalang Node
         - list of javalang Nodes and other such lists (with any depth)
        """
        for node, attributes in self._graph.nodes.items():
            for attribute_name in attributes:
                attribute_value = attributes[attribute_name]
                if isinstance(attribute_value, Node):
                    node_reference = self._create_reference_to_node(attribute_value)
                    self._graph.add_node(node, **{attribute_name: node_reference})
                elif isinstance(attribute_value, list):
                    node_references = self._replace_javalang_nodes_in_list(attribute_value)
                    self._graph.add_node(node, **{attribute_name: node_references})

    def _replace_javalang_nodes_in_list(self, javalang_nodes_list: List[Any]) -> List[Any]:
        """
        javalang_nodes_list: list of javalang Nodes or other such lists (with any depth)
        All javalang nodes are replaces with according references
        NOTICE: Any is used, because mypy does not support recurrent type definitions
        """
        node_references_list: List[Any] = []
        for item in javalang_nodes_list:
            if isinstance(item, Node):
                node_references_list.append(self._create_reference_to_node(item))
            elif isinstance(item, list):
                node_references_list.append(self._replace_javalang_nodes_in_list(item))
            elif isinstance(item, (int, str)) or item is None:
                node_references_list.append(item)
            else:
                raise RuntimeError(
                    f"Cannot parse Javalang attribute:\n{item}\nExpected: Node, list of Nodes, integer or string"
                )

        return node_references_list

    def _create_reference_to_node(self, javalang_node: Node) -> ASTNodeReference:
        return ASTNodeReference(self._javalang_node_to_index_map[javalang_node])

    _UNKNOWN_NODE_TYPE = -1
