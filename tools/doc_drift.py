"""Docstring drift checker for src/drafter.

Complements ruff's D rules (presence) with the two drift checks ruff does not
have: Google-style ``Args:`` sections compared against the actual function
signature, and ``Attributes:`` sections compared against the class's declared
fields. These catch the audit's dominant failure modes: phantom parameters left
behind by refactors, and dataclass fields added after the class docstring was
written.

Run from the repo root::

    python tools/doc_drift.py

Prints one line per finding and exits non-zero if any were found (wired into
the lint job in .github/workflows/test_and_lint.yml).
"""

import ast
import re
import sys
from pathlib import Path

ROOT = Path("src")

# Matches a Google-style section entry like "name (type): desc" or "name: desc",
# including *args/**kwargs forms.
ENTRY_RE = re.compile(r"^(\*{0,2}\w+)(?:\s*\([^)]*\))?:")

SECTION_HEADERS = {
    "Args:",
    "Arguments:",
    "Attributes:",
    "Returns:",
    "Yields:",
    "Raises:",
    "Example:",
    "Examples:",
    "Note:",
    "Notes:",
    "Warning:",
    "Warns:",
    "See Also:",
    "Todo:",
}


def parse_section(docstring, header):
    """Extract the entry names of one Google-style section from a docstring.

    Args:
        docstring: The cleaned docstring text (from ``ast.get_docstring``).
        header: Section header to look for, e.g. ``"Args:"``.

    Returns:
        A list of entry names with any ``*``/``**`` prefixes stripped, or None
        if the section is absent.
    """
    lines = docstring.splitlines()
    try:
        start = next(i for i, line in enumerate(lines) if line.strip() == header)
    except StopIteration:
        return None
    names = []
    entry_indent = None
    for line in lines[start + 1 :]:
        if not line.strip():
            continue
        indent = len(line) - len(line.lstrip())
        if indent == 0:
            break  # next section (or dedented prose) ends this one
        if entry_indent is None:
            entry_indent = indent
        if indent > entry_indent:
            continue  # continuation of the previous entry's description
        match = ENTRY_RE.match(line.strip())
        if match:
            names.append(match.group(1).lstrip("*"))
    return names


def signature_params(node):
    """Collect a function's parameter names, excluding self/cls.

    Args:
        node: A FunctionDef or AsyncFunctionDef node.

    Returns:
        A list of parameter names, with vararg/kwarg included un-starred.
    """
    args = node.args
    names = [a.arg for a in args.posonlyargs + args.args + args.kwonlyargs]
    if args.vararg:
        names.append(args.vararg.arg)
    if args.kwarg:
        names.append(args.kwarg.arg)
    is_static = any(
        isinstance(d, ast.Name) and d.id == "staticmethod" for d in node.decorator_list
    )
    if names and names[0] in ("self", "cls") and not is_static:
        names = names[1:]
    return names


def is_dataclass(node):
    """Whether a ClassDef carries a @dataclass decorator (bare or called)."""
    for d in node.decorator_list:
        target = d.func if isinstance(d, ast.Call) else d
        name = (
            target.attr
            if isinstance(target, ast.Attribute)
            else getattr(target, "id", None)
        )
        if name == "dataclass":
            return True
    return False


def class_field_info(node):
    """Gather a class's declared attribute names.

    Args:
        node: A ClassDef node.

    Returns:
        A tuple ``(fields, all_attrs, string_documented)`` where ``fields``
        are annotated non-ClassVar class-body names (dataclass fields when
        the class is a dataclass), ``all_attrs`` additionally includes
        ClassVar names, plain class-body assignments, properties, and
        ``self.x`` assignments in methods, and ``string_documented`` are the
        fields carrying a PEP-224-style string doc after their assignment.
    """
    fields = []
    all_attrs = set()
    string_documented = set()
    for i, item in enumerate(node.body):
        if isinstance(item, ast.AnnAssign) and isinstance(item.target, ast.Name):
            all_attrs.add(item.target.id)
            annotation = ast.unparse(item.annotation)
            if "ClassVar" not in annotation:
                fields.append(item.target.id)
            nxt = node.body[i + 1] if i + 1 < len(node.body) else None
            if (
                isinstance(nxt, ast.Expr)
                and isinstance(nxt.value, ast.Constant)
                and isinstance(nxt.value.value, str)
            ):
                string_documented.add(item.target.id)
        elif isinstance(item, ast.Assign):
            all_attrs.update(t.id for t in item.targets if isinstance(t, ast.Name))
        elif isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
            if any(
                isinstance(d, ast.Name) and d.id == "property"
                for d in item.decorator_list
            ):
                all_attrs.add(item.name)
            for sub in ast.walk(item):
                if isinstance(sub, ast.Attribute) and isinstance(sub.ctx, ast.Store):
                    if isinstance(sub.value, ast.Name) and sub.value.id == "self":
                        all_attrs.add(sub.attr)
    return fields, all_attrs, string_documented


def base_names(node):
    """The simple names of a ClassDef's base classes."""
    names = []
    for base in node.bases:
        if isinstance(base, ast.Name):
            names.append(base.id)
        elif isinstance(base, ast.Attribute):
            names.append(base.attr)
        elif isinstance(base, ast.Subscript):  # Generic[...] etc.
            names.append(getattr(base.value, "id", ""))
    return names


def check_function(path, node, findings, prefix=""):
    """Check one function's Args section against its signature."""
    docstring = ast.get_docstring(node)
    if not docstring:
        return
    documented = parse_section(docstring, "Args:")
    if documented is None:
        documented = parse_section(docstring, "Arguments:")
    if documented is None:
        return
    actual = signature_params(node)
    label = f"{prefix}{node.name}"
    for name in documented:
        if name not in actual:
            findings.append(
                f"{path}:{node.lineno}: {label}: documented arg '{name}' "
                f"is not in the signature"
            )
    for name in actual:
        if name.startswith("_"):
            continue
        if name not in documented:
            findings.append(
                f"{path}:{node.lineno}: {label}: arg '{name}' missing from Args section"
            )


def inherited_attrs(class_name, registry, seen=None):
    """All attribute names reachable through a class's (resolvable) bases."""
    if seen is None:
        seen = set()
    if class_name in seen or class_name not in registry:
        return set()
    seen.add(class_name)
    node = registry[class_name]
    _, attrs, _ = class_field_info(node)
    for base in base_names(node):
        attrs |= inherited_attrs(base, registry, seen)
    return attrs


def main():
    """Scan src/ for docstring drift and report findings.

    Returns:
        Process exit code: 0 when clean, 1 when findings were reported.
    """
    findings = []
    registry = {}
    trees = {}
    for path in sorted(ROOT.rglob("*.py")):
        try:
            tree = ast.parse(path.read_text(encoding="utf-8", errors="replace"))
        except SyntaxError as error:
            findings.append(f"{path}: syntax error: {error}")
            continue
        trees[path] = tree
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                registry.setdefault(node.name, node)

    for path, tree in trees.items():
        for node in tree.body:
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                check_function(path, node, findings)
        for node in ast.walk(tree):
            if not isinstance(node, ast.ClassDef):
                continue
            for item in node.body:
                if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    check_function(path, item, findings, prefix=f"{node.name}.")
            docstring = ast.get_docstring(node)
            if not docstring:
                continue
            documented = parse_section(docstring, "Attributes:")
            if documented is None:
                continue
            fields, own_attrs, string_documented = class_field_info(node)
            known = set(own_attrs)
            for base in base_names(node):
                known |= inherited_attrs(base, registry)
            for name in documented:
                if name not in known:
                    findings.append(
                        f"{path}:{node.lineno}: {node.name}: documented attribute "
                        f"'{name}' is not defined on the class (or its bases)"
                    )
            if is_dataclass(node):
                for name in fields:
                    if (
                        not name.startswith("_")
                        and name not in documented
                        and name not in string_documented
                    ):
                        findings.append(
                            f"{path}:{node.lineno}: {node.name}: field '{name}' "
                            f"missing from Attributes section"
                        )

    for finding in findings:
        print(finding)
    print(f"{len(findings)} drift finding(s).")
    return 1 if findings else 0


if __name__ == "__main__":
    sys.exit(main())
