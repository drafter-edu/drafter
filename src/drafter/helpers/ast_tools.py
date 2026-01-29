from typing import Optional
import ast


class ExtentGetter(ast.NodeVisitor):
    """Collect line extents for AST nodes in a source tree.

    Attributes:
        extents: Cached extent information if provided externally.
        line_map: Mapping of AST nodes to (start, end) line pairs.
        node_stack: Traversal stack of ancestor nodes used for extent propagation.
    """

    def __init__(self):
        """Initialize storage for line extents and traversal state."""
        self.extents = None
        # Map nodes to line start/stop
        self.line_map = {}
        self.node_stack = []

    def check_all(self, node):
        """Visit all nodes to populate line extents.

        Args:
            node: Root AST node to traverse.
        """
        self.visit(node)

    def update_parents(self, node, start: int, end: int):
        """Propagate child extent updates to ancestor nodes.

        Args:
            node: Current AST node whose parents will be updated.
            start: Lowest line number observed in the child.
            end: Highest line number observed in the child.
        """
        for parent_node in self.node_stack:
            if parent_node in self.line_map:
                original_lowest, original_highest = self.line_map[parent_node]
                self.line_map[parent_node] = (
                    min(original_lowest, start),
                    max(original_highest, end),
                )

    def visit(self, node: ast.AST):
        """Record extent for a node and continue traversal."""
        try:
            self.line_map[node] = (node.lineno, node.end_lineno)  # type: ignore
            self.update_parents(node, node.lineno, node.end_lineno)  # type: ignore
        except Exception as e:
            pass  # print(e)
        self.node_stack.append(node)
        ast.NodeVisitor.visit(self, node)
        self.node_stack.pop()

    def get_lines(self, lineno: int) -> tuple[int, int]:
        """Return bounding lines for the node covering the given line.

        Args:
            lineno: Line number to locate.

        Returns:
            Start and end line numbers that encompass the provided line.
        """
        lowest, highest = lineno, lineno
        for node, (start, end) in self.line_map.items():
            if start <= lineno <= end:
                lowest = min(lowest, start)
                highest = max(highest, end)
        return lowest, highest


_cache = {}


def get_all_relevant_lines(lineno: int, code: str) -> str:
    """Extract code block covering the AST node at a specific line.

    Args:
        lineno: Line number used to locate the enclosing node.
        code: Full source code to analyze.

    Returns:
        A string containing all lines that belong to the node covering lineno.
    """
    if code in _cache:
        getter = _cache[code]
    else:
        tree = ast.parse(code)
        getter = ExtentGetter()
        getter.check_all(tree)
        _cache[code] = getter
    start, end = getter.get_lines(lineno)
    code_lines = code.splitlines()
    result = "\n".join(code_lines[start - 1 : end])
    return result
