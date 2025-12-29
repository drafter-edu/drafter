'''
Returns a dictionary with at least the fields: name, type, value
'''

from dataclasses import fields, is_dataclass
from typing import Any

from drafter.history.utils import safe_repr


class RecursiveTypeDescriber:
    """Utility to describe nested Python structures as nested tables.

    - Expands dataclasses, dicts, lists/tuples recursively
    - Detects cycles and emits a placeholder
    - Limits recursion with max_depth
    - Produces a JSON-friendly "table" structure
    """

    def __init__(self, *, max_depth: int = 4, list_ellipsis_length = 10) -> None:
        self.max_depth: int = max_depth
        self.list_ellipsis_length: int = list_ellipsis_length
        self._seen: set[int] = set()

    @staticmethod
    def value_type(value: Any) -> str:
        try:
            return value.__class__.__name__
        except Exception:
            return type(value).__name__

    def _row(self, name: str, value: Any) -> dict[str, Any]:
        return {
            "name": name or "(state)",
            "type": self.value_type(value),
            "value": safe_repr(value),
        }

    def _walk(self, value: Any, name: str, depth: int) -> dict[str, Any]:
        # Prevent infinite recursion on cyclic refs
        try:
            obj_id = id(value)
        except Exception:
            obj_id = None
        if obj_id is not None:
            if obj_id in self._seen:
                return {
                    "name": name or "(state)",
                    "type": self.value_type(value),
                    "value": "<cycle>",
                }
            self._seen.add(obj_id)

        # Stop at max depth
        if depth > self.max_depth:
            return self._row(name, value)

        # Dataclass expansion
        if is_dataclass(value):
            rows: list[dict[str, Any]] = []
            for f in fields(value):
                child = getattr(value, f.name)
                child_row = self._walk(child, f"{name}.{f.name}" if name else f.name, depth + 1)
                rows.append(child_row)
            return {
                "name": name or "(state)",
                "type": self.value_type(value),
                "value": {
                    "columns": ["Field", "Type", "Value"],
                    "rows": rows,
                },
            }

        # Dict expansion
        if isinstance(value, dict):
            rows: list[dict[str, Any]] = []
            for k, v in value.items():
                key_name = str(k)
                child_row = self._walk(v, f"{name}.{key_name}" if name else key_name, depth + 1)
                rows.append(child_row)
            return {
                "name": name or "(state)",
                "type": self.value_type(value),
                "value": {
                    "columns": ["Field", "Type", "Value"],
                    "rows": rows,
                },
            }

        # List/Tuple expansion
        if isinstance(value, (list, tuple)):
            rows: list[dict[str, Any]] = []
            length = len(value)
            if length > self.list_ellipsis_length:
                indices = list(range(self.list_ellipsis_length // 2)) + ["..."] + list(
                    range(length - self.list_ellipsis_length // 2, length)
                )
            else:
                indices = range(length)
            for idx in indices:
                if idx == "...":
                    rows.append({
                        "name": f"{name}[...]" if name else "[...]",
                        "type": "ellipsis",
                        "value": "...",
                    })
                else:
                    child_row = self._walk(value[idx], f"{name}[{idx}]" if name else f"[{idx}]", depth + 1)  # type: ignore
                    rows.append(child_row)
            return {
                "name": name or "(state)",
                "type": self.value_type(value),
                "value": {
                    "columns": ["Field", "Type", "Value"],
                    "rows": rows,
                },
            }

        # Primitive or other object: record leaf
        return self._row(name, value)

    def describe_table(self, state: Any) -> dict[str, Any]:
        """Return a nested table structure for the given state.

        Schema:
        {
          "columns": ["Field", "Type", "Value"],
          "rows": [
             { "name": str, "type": str, "value": str | Table }
          ]
        }
        """
        self._seen = set()
        top_row = self._walk(state, "", 0)
        return {
            "columns": ["Field", "Type", "Value"],
            "rows": [top_row],
        }
