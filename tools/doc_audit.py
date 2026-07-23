"""AST-based docstring coverage audit for src/drafter."""
import ast, sys, json
from pathlib import Path

ROOT = Path("src")

def is_public(name):
    return not name.startswith("_") or name in ("__init__",)

def audit_file(path):
    src = path.read_text(encoding="utf-8", errors="replace")
    try:
        tree = ast.parse(src)
    except SyntaxError as e:
        return {"file": str(path), "error": str(e)}
    stats = {
        "file": str(path).replace("\\", "/"),
        "module_doc": ast.get_docstring(tree) is not None,
        "classes": 0, "classes_doc": 0,
        "funcs": 0, "funcs_doc": 0,
        "methods": 0, "methods_doc": 0,
        "consts": 0, "consts_doc": 0,
        "missing": [],
    }
    # top-level constants: Assign/AnnAssign at module level with UPPER or plain names,
    # documented if followed by a string Expr
    body = tree.body
    for i, node in enumerate(body):
        targets = []
        if isinstance(node, ast.Assign):
            targets = [t.id for t in node.targets if isinstance(t, ast.Name)]
        elif isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
            targets = [node.target.id]
        if targets and any(is_public(t) and t != "__all__" for t in targets):
            stats["consts"] += 1
            nxt = body[i+1] if i+1 < len(body) else None
            documented = isinstance(nxt, ast.Expr) and isinstance(nxt.value, ast.Constant) and isinstance(nxt.value.value, str)
            if documented:
                stats["consts_doc"] += 1
            else:
                stats["missing"].append(f"const:{targets[0]}:{node.lineno}")

    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef):
            if is_public(node.name):
                stats["classes"] += 1
                if ast.get_docstring(node):
                    stats["classes_doc"] += 1
                else:
                    stats["missing"].append(f"class:{node.name}:{node.lineno}")
                # methods
                for item in node.body:
                    if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)) and is_public(item.name) and item.name != "__init__":
                        stats["methods"] += 1
                        if ast.get_docstring(item):
                            stats["methods_doc"] += 1
                        else:
                            stats["missing"].append(f"method:{node.name}.{item.name}:{item.lineno}")
    for node in body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and is_public(node.name):
            stats["funcs"] += 1
            if ast.get_docstring(node):
                stats["funcs_doc"] += 1
            else:
                stats["missing"].append(f"func:{node.name}:{node.lineno}")
    if not stats["module_doc"]:
        stats["missing"].insert(0, "module:1")
    return stats

results = [audit_file(p) for p in sorted(ROOT.rglob("*.py"))]
print(json.dumps(results, indent=1))
