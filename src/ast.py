from collections import defaultdict
from enum import Enum, auto
from typing import Union, Callable, List, Dict, Optional, Set, TYPE_CHECKING

from networkx import DiGraph, dfs_labeled_edges, dfs_preorder_nodes  # type: ignore

from .ast_node_type import ASTNodeType
from .ast_node import ASTNode
from ._ast_builder import AstBuilder

if TYPE_CHECKING:
    from pathlib import Path  # noqa: F401

TraverseCallback = Callable[[ASTNode], None]


class NodesSearchFilter(Enum):
    TOP_LEVEL = auto()
    BOTTOM_LEVEL = auto()
    ALL = auto()


class AST:
    def __init__(self, networkx_tree: DiGraph, root: int):
        self.tree = networkx_tree
        self.root = root

    @staticmethod
    def build(source_code_file_path: Union[str, "Path"]) -> "AST":
        builder = AstBuilder()
        graph, root_id = builder.build(source_code_file_path)
        return AST(graph, root_id)

    def find_nodes(self, *node_types: ASTNodeType, search_filter=NodesSearchFilter.ALL) -> List[ASTNode]:
        if search_filter == NodesSearchFilter.ALL:
            return self._find_nodes(*node_types)
        elif search_filter == NodesSearchFilter.TOP_LEVEL:
            return self._find_top_level_nodes(*node_types)
        elif search_filter == NodesSearchFilter.BOTTOM_LEVEL:
            return self._find_bottom_level_nodes(*node_types)
        else:
            raise NotImplementedError(f"Unknown search filter {search_filter}.")

    @property
    def nodes(self) -> List[ASTNode]:
        return [ASTNode(self.tree, node_id) for node_id in self.tree.nodes]

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

    def _find_nodes(self, *node_types: ASTNodeType) -> List[ASTNode]:
        return [
            ASTNode(self.tree, node_id)
            for node_id in self.tree.nodes
            if not node_types or self._get_node_type(node_id) in node_types
        ]

    def _find_top_level_nodes(self, *node_types: ASTNodeType) -> List[ASTNode]:
        # if all node types are valid than there is only one single top level node
        # and it is root
        if not node_types:
            return [self.get_root()]

        nodes: List[ASTNode] = []
        current_node: Optional[ASTNode] = None

        def on_node_entering(node: ASTNode) -> None:
            nonlocal current_node, nodes
            if not current_node and node.node_type in node_types:
                nodes.append(node)
                current_node = node

        def on_node_leaving(node: ASTNode) -> None:
            nonlocal current_node, nodes
            if current_node and node == current_node:
                current_node = None

        self.traverse(on_node_entering, on_node_leaving)
        return nodes

    def _find_bottom_level_nodes(self, *node_types: ASTNodeType) -> List[ASTNode]:
        nodes: List[ASTNode] = []
        nodes_stack: List[ASTNode] = []
        not_bottom_nodes: Set[ASTNode] = set()

        def on_node_entering(node: ASTNode) -> None:
            nonlocal nodes_stack
            if not node_types or node.node_type in node_types:
                nodes_stack.append(node)

        def on_node_leaving(node: ASTNode) -> None:
            nonlocal nodes_stack, not_bottom_nodes, nodes
            if not node_types or node.node_type in node_types:
                if node not in not_bottom_nodes:
                    nodes.append(node)

                nodes_stack.pop()
                not_bottom_nodes.update(nodes_stack)

        self.traverse(on_node_entering, on_node_leaving)
        return nodes

    def _get_node_type(self, node_id: int) -> ASTNodeType:
        return self.tree.nodes[node_id]["node_type"]

    _fake_nodes_qty_per_graph: Dict[DiGraph, int] = defaultdict(lambda: 0)
