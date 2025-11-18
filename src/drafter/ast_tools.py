from typing import Optional
import ast


class ExtentGetter(ast.NodeVisitor):
    def __init__(self):
        self.extents = None
        # Map nodes to line start/stop
        self.line_map = {}
        self.node_stack = []

    def check_all(self, node):
        self.visit(node)

    def update_parents(self, node, start: int, end: int):
        for parent_node in self.node_stack:
            if parent_node in self.line_map:
                original_lowest, original_highest = self.line_map[parent_node]
                self.line_map[parent_node] = update = (
                    min(original_lowest, start),
                    max(original_highest, end),
                )

    def visit(self, node: ast.AST):
        try:
            self.line_map[node] = (node.lineno, node.end_lineno)  # type: ignore
            self.update_parents(node, node.lineno, node.end_lineno)  # type: ignore
        except Exception as e:
            pass  # print(e)
        self.node_stack.append(node)
        ast.NodeVisitor.visit(self, node)
        self.node_stack.pop()

    def get_lines(self, lineno: int) -> tuple[int, int]:
        lowest, highest = lineno, lineno
        for node, (start, end) in self.line_map.items():
            if start <= lineno <= end:
                lowest = min(lowest, start)
                highest = max(highest, end)
        return lowest, highest


_cache = {}


def get_all_relevant_lines(lineno: int, code: str) -> str:
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
