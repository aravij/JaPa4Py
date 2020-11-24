from collections import defaultdict
from typing import Union, Any, Callable, Set, List, Iterator, Tuple, Dict, cast, Optional, TYPE_CHECKING

from networkx import DiGraph, dfs_labeled_edges, dfs_preorder_nodes  # type: ignore
from javalang.tree import Node

from .ast_node_type import ASTNodeType
from .ast_node import ASTNode
from .utils.ast_builder import build_ast
from ._auxiliary_data import (
    javalang_to_ast_node_type,
    attributes_by_node_type,
    ASTNodeReference,
)

if TYPE_CHECKING:
    from pathlib import Path

TraverseCallback = Callable[[ASTNode], None]


class AST:
    def __init__(self, networkx_tree: DiGraph, root: int):
        self.tree = networkx_tree
        self.root = root

    @staticmethod
    def build_from_javalang(java_source_code_file_path: Union[str, "Path"]) -> "AST":
        javalang_ast_root = build_ast(java_source_code_file_path)
        tree = DiGraph()
        javalang_node_to_index_map: Dict[Node, int] = {}
        root = AST._add_subtree_from_javalang_node(tree, javalang_ast_root, javalang_node_to_index_map)
        AST._replace_javalang_nodes_in_attributes(tree, javalang_node_to_index_map)
        return AST(tree, root)

    def __str__(self) -> str:
        printed_graph = ""
        depth = 0
        for _, destination, edge_type in dfs_labeled_edges(self.tree, self.root):
            if edge_type == "forward":
                printed_graph += "|   " * depth
                node_type = self.tree.nodes[destination]["node_type"]
                printed_graph += str(node_type) + ": "
                if node_type == ASTNodeType.STRING:
                    printed_graph += self.tree.nodes[destination]["string"] + ", "
                printed_graph += f"node index = {destination}"
                node_line = self.tree.nodes[destination]["line"]
                if node_line is not None:
                    printed_graph += f", line = {node_line}"
                printed_graph += "\n"
                depth += 1
            elif edge_type == "reverse":
                depth -= 1
        return printed_graph

    def get_root(self) -> ASTNode:
        return ASTNode(self.tree, self.root)

    def __iter__(self) -> Iterator[ASTNode]:
        for node_index in self.tree.nodes:
            yield ASTNode(self.tree, node_index)

    def get_subtrees(self, *root_type: ASTNodeType) -> Iterator["AST"]:
        """
        Yields subtrees with given type of the root.
        If such subtrees are one including the other, only the larger one is
        going to be in resulted sequence.
        """
        is_inside_subtree = False
        current_subtree_root = -1  # all node indexes are positive
        subtree: List[int] = []
        for _, destination, edge_type in dfs_labeled_edges(self.tree, self.root):
            if edge_type == "forward":
                if is_inside_subtree:
                    subtree.append(destination)
                elif self.tree.nodes[destination]["node_type"] in root_type:
                    subtree.append(destination)
                    is_inside_subtree = True
                    current_subtree_root = destination
            elif edge_type == "reverse" and destination == current_subtree_root:
                is_inside_subtree = False
                yield AST(self.tree.subgraph(subtree), current_subtree_root)
                subtree = []
                current_subtree_root = -1

    def get_subtree(self, node: ASTNode) -> "AST":
        subtree_nodes_indexes = dfs_preorder_nodes(self.tree, node.node_index)
        subtree = self.tree.subgraph(subtree_nodes_indexes)
        return AST(subtree, node.node_index)

    def traverse(
        self,
        on_node_entering: TraverseCallback,
        on_node_leaving: TraverseCallback = lambda node: None,
        source_node: Optional[ASTNode] = None,
        undirected=False,
    ):
        traverse_graph = self.tree.to_undirected(as_view=True) if undirected else self.tree
        if source_node is None:
            source_node = self.get_root()

        for _, destination, edge_type in dfs_labeled_edges(traverse_graph, source_node.node_index):
            if edge_type == "forward":
                on_node_entering(ASTNode(self.tree, destination))
            elif edge_type == "reverse":
                on_node_leaving(ASTNode(self.tree, destination))

    def create_fake_node(self) -> ASTNode:
        fake_nodes_qty = self._fake_nodes_qty_per_graph[self.tree]
        self._fake_nodes_qty_per_graph[self.tree] += 1
        new_fake_node_id = -(fake_nodes_qty + 1)
        return ASTNode(self.tree, new_fake_node_id)

    def get_proxy_nodes(self, *types: ASTNodeType) -> Iterator[ASTNode]:
        for node in self.tree.nodes:
            if len(types) == 0 or self.tree.nodes[node]["node_type"] in types:
                yield ASTNode(self.tree, node)

    @staticmethod
    def _add_subtree_from_javalang_node(
        tree: DiGraph,
        javalang_node: Union[Node, Set[Any], str],
        javalang_node_to_index_map: Dict[Node, int],
    ) -> int:
        node_index, node_type = AST._add_javalang_node(tree, javalang_node)
        if node_index != AST._UNKNOWN_NODE_TYPE and node_type not in {
            ASTNodeType.COLLECTION,
            ASTNodeType.STRING,
        }:
            javalang_standard_node = cast(Node, javalang_node)
            javalang_node_to_index_map[javalang_standard_node] = node_index
            AST._add_javalang_children(
                tree,
                javalang_standard_node.children,
                node_index,
                javalang_node_to_index_map,
            )
        return node_index

    @staticmethod
    def _add_javalang_children(
        tree: DiGraph,
        children: List[Any],
        parent_index: int,
        javalang_node_to_index_map: Dict[Node, int],
    ) -> None:
        for child in children:
            if isinstance(child, list):
                AST._add_javalang_children(tree, child, parent_index, javalang_node_to_index_map)
            else:
                child_index = AST._add_subtree_from_javalang_node(tree, child, javalang_node_to_index_map)
                if child_index != AST._UNKNOWN_NODE_TYPE:
                    tree.add_edge(parent_index, child_index)

    @staticmethod
    def _add_javalang_node(tree: DiGraph, javalang_node: Union[Node, Set[Any], str]) -> Tuple[int, ASTNodeType]:
        node_index = AST._UNKNOWN_NODE_TYPE
        node_type = ASTNodeType.UNKNOWN
        if isinstance(javalang_node, Node):
            node_index, node_type = AST._add_javalang_standard_node(tree, javalang_node)
        elif isinstance(javalang_node, set):
            node_index = AST._add_javalang_collection_node(tree, javalang_node)
            node_type = ASTNodeType.COLLECTION
        elif isinstance(javalang_node, str):
            node_index = AST._add_javalang_string_node(tree, javalang_node)
            node_type = ASTNodeType.STRING

        return node_index, node_type

    @staticmethod
    def _add_javalang_standard_node(tree: DiGraph, javalang_node: Node) -> Tuple[int, ASTNodeType]:
        node_index = len(tree) + 1
        node_type = javalang_to_ast_node_type[type(javalang_node)]

        attr_names = attributes_by_node_type[node_type]
        attributes = {attr_name: getattr(javalang_node, attr_name) for attr_name in attr_names}

        attributes["node_type"] = node_type
        attributes["line"] = javalang_node.position.line if javalang_node.position is not None else None

        AST._post_process_javalang_attributes(tree, node_type, attributes)

        tree.add_node(node_index, **attributes)
        return node_index, node_type

    @staticmethod
    def _post_process_javalang_attributes(tree: DiGraph, node_type: ASTNodeType, attributes: Dict[str, Any]) -> None:
        """
        Replace some attributes with more appropriate values for convenient work
        """

        if node_type == ASTNodeType.METHOD_DECLARATION and attributes["body"] is None:
            attributes["body"] = []

        if node_type == ASTNodeType.LAMBDA_EXPRESSION and isinstance(attributes["body"], Node):
            attributes["body"] = [attributes["body"]]

        if node_type in {ASTNodeType.METHOD_INVOCATION, ASTNodeType.MEMBER_REFERENCE} and attributes["qualifier"] == "":
            attributes["qualifier"] = None

    @staticmethod
    def _add_javalang_collection_node(tree: DiGraph, collection_node: Set[Any]) -> int:
        node_index = len(tree) + 1
        tree.add_node(node_index, node_type=ASTNodeType.COLLECTION, line=None)
        # we expect only strings in collection
        # we add them here as children
        for item in collection_node:
            if type(item) == str:
                string_node_index = AST._add_javalang_string_node(tree, item)
                tree.add_edge(node_index, string_node_index)
            elif item is not None:
                raise ValueError(
                    'Unexpected javalang AST node type {} inside \
                                 "COLLECTION" node'.format(
                        type(item)
                    )
                )
        return node_index

    @staticmethod
    def _add_javalang_string_node(tree: DiGraph, string_node: str) -> int:
        node_index = len(tree) + 1
        tree.add_node(node_index, node_type=ASTNodeType.STRING, string=string_node, line=None)
        return node_index

    @staticmethod
    def _replace_javalang_nodes_in_attributes(tree: DiGraph, javalang_node_to_index_map: Dict[Node, int]) -> None:
        """
        All javalang nodes found in networkx nodes attributes are replaced
        with references to according networkx nodes.
        Supported attributes types:
         - just javalang Node
         - list of javalang Nodes and other such lists (with any depth)
        """
        for node, attributes in tree.nodes.items():
            for attribute_name in attributes:
                attribute_value = attributes[attribute_name]
                if isinstance(attribute_value, Node):
                    node_reference = AST._create_reference_to_node(attribute_value, javalang_node_to_index_map)
                    tree.add_node(node, **{attribute_name: node_reference})
                elif isinstance(attribute_value, list):
                    node_references = AST._replace_javalang_nodes_in_list(attribute_value, javalang_node_to_index_map)
                    tree.add_node(node, **{attribute_name: node_references})

    @staticmethod
    def _replace_javalang_nodes_in_list(
        javalang_nodes_list: List[Any], javalang_node_to_index_map: Dict[Node, int]
    ) -> List[Any]:
        """
        javalang_nodes_list: list of javalang Nodes or other such lists (with any depth)
        All javalang nodes are replaces with according references
        NOTICE: Any is used, because mypy does not support recurrent type definitions
        """
        node_references_list: List[Any] = []
        for item in javalang_nodes_list:
            if isinstance(item, Node):
                node_references_list.append(AST._create_reference_to_node(item, javalang_node_to_index_map))
            elif isinstance(item, list):
                node_references_list.append(AST._replace_javalang_nodes_in_list(item, javalang_node_to_index_map))
            elif isinstance(item, (int, str)) or item is None:
                node_references_list.append(item)
            else:
                raise RuntimeError(
                    'Cannot parse "Javalang" attribute:\n'
                    f"{item}\n"
                    "Expected: Node, list of Nodes, integer or string"
                )

        return node_references_list

    @staticmethod
    def _create_reference_to_node(javalang_node: Node, javalang_node_to_index_map: Dict[Node, int]) -> ASTNodeReference:
        return ASTNodeReference(javalang_node_to_index_map[javalang_node])

    _UNKNOWN_NODE_TYPE = -1

    _fake_nodes_qty_per_graph: Dict[DiGraph, int] = defaultdict(lambda: 0)
