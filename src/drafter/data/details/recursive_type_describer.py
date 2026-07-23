"""Recursive description of Python values for the debug UI.

Walks arbitrarily nested Python data (primitives, tuples, lists/sets,
dicts, dataclasses, and Pillow images) and produces JSON-friendly
"representation" dictionaries that the client renders as nested tables
of values and types (e.g., a `list[Dog]` becomes rows of field/value
pairs; a 2D homogenous list becomes a grid).

Every representation dict has at least:

- `kind`: which shape of representation this is (e.g. `primitive`,
  `tuple`, `homogenous_linear_collection`, `homogenous_grid`, `dict`,
  `dataclass`, `cycle_reference`, `max_depth_reached`, `unknown`,
  `error`).
- `type`: the value's class name. Collections may also carry
  `elementType`/`keyType`/`valueType` and a `fullType` such as
  `list[int]` or `dict[str, int]`.
- `id`: the `id()` of the value (cycle references instead carry
  `targetId`, pointing at the already-described object).
- `complexity`: a rough integer score of how complicated the value is,
  used to give students meaningful explanations of their state.

Depending on `kind`, a dict also carries the described children:
`value` for primitives, `elements` for tuples/lists/sets, `rows` for
2D grids, `entries` (key/value pairs) for dicts, and `fields`
(name/value pairs) for dataclasses. Cycles are reported as
`cycle_reference` nodes rather than recursed into, and traversal stops
at a configurable maximum depth.
"""

# Roadmap of value kinds not yet specially handled (they currently fall
# through to the generic "unknown" repr, or to a structural handler that
# loses type-specific detail):
# - namedtuple (described as a plain tuple) and TypedDict (plain dict)
# - non-dataclass class instances
# - declared type unions: Optional, Union
# - files: pathlib.Path, io.StringIO, io.BytesIO,
#   DrafterBinaryFile/DrafterTextFile
# - Drafter components (types with custom reprs)
# - binary data: bytes, bytearray
# - functions/methods/lambdas; iterators/generators/range/enumerate
# - meta types (type, module); Literal; Any/Never; exceptions
# Also planned: truncating large lists to the first/last N items with an
# ellipsis in between, and using the complexity score as a heuristic for
# when to trigger IndexDB storage of state snapshots.

from dataclasses import fields, is_dataclass
from typing import Any

from drafter.components.utilities.image_support import HAS_PILLOW, PILImage


def first_shared_base(cls1, cls2):
    """
    Return the first shared base class in the MROs of cls1 and cls2.

    Args:
        cls1: The first class to compare.
        cls2: The second class to compare.

    Returns:
        The first class in cls1's MRO that also appears in cls2's MRO,
        or None if they share no base class.
    """
    mro1 = cls1.__mro__
    mro2 = cls2.__mro__

    for cls in mro1:
        if cls in mro2:
            return cls

    return None


class TypeFlattener:
    """Collects the element types seen in a collection and flattens them
    into a single classification.

    Used while describing lists, sets, and dicts to decide whether a
    collection is homogenous (one element type), a union of types, or empty.

    Attributes:
        _types: The set of type-name strings recorded so far.
    """

    # TODO: Need to handle shared common ancestors, collection types
    # Should also be checking the actual types of things, not just the
    # string representation
    def __init__(self):
        self._types: set[str] = set()

    def add_type(self, representation: dict):
        """
        Records the type of one described element.

        Args:
            representation: A representation dict for the element; its
                `fullType` (or, failing that, `type`) field is recorded.
        """
        full_type = representation.get(
            "fullType", representation.get("type", "unknown")
        )
        self._types.add(full_type)

    def flatten(self) -> tuple[str, list[str]]:
        """
        Flattens the recorded types into a single classification.

        Returns:
            A tuple of a kind and a list of type names: ("homogenous",
            [the single type]) when exactly one type was recorded,
            ("union", sorted types) when several were, or ("none", [])
            when no elements were recorded.
        """
        if len(self._types) == 1:
            return "homogenous", [self._types.pop()]
        elif len(self._types) > 1:
            return "union", sorted(self._types)
        else:
            return "none", []


class RecursiveTypeDescriber:
    """Describes nested Python values as JSON-friendly representation dicts.

    Recursively walks a value, producing one representation dict per node
    (see the module docstring for the dict fields). Cycles are reported as
    `cycle_reference` nodes, and traversal past `max_depth` is reported as
    `max_depth_reached` nodes.

    Attributes:
        max_depth: Maximum recursion depth before traversal stops.
    """

    def __init__(self, *, max_depth: int = 5) -> None:
        self.max_depth: int = max_depth

    def analyze(self, value: Any) -> dict[str, Any]:
        """Describe a value as a nested representation dict.

        Never raises: any failure during analysis is captured and returned
        as an `error` representation dict (or a `complete_failure` dict if
        even the error reporting fails).

        Args:
            value: The Python value to describe.

        Returns:
            A representation dict with at least `kind`, `type`, and
            `complexity` fields; most kinds also carry the value's `id` and
            kind-specific children such as `value`, `elements`, `rows`,
            `entries`, or `fields` (see the module docstring).
        """
        try:
            result = self._walk(value, 0, set())
            return result
        except Exception as e:
            try:
                return self._visit_error(value, e)
            except Exception as new_e:
                return self._visit_complete_failure(value, e, new_e)

    @staticmethod
    def value_type(value: Any) -> str:
        """
        Best-effort class name of a value.

        Args:
            value: The value whose class name to look up.

        Returns:
            The value's class name, falling back to `type(value)` when the
            value's own attribute access fails.
        """
        try:
            return value.__class__.__name__
        except Exception:
            return type(value).__name__

    def _visit_error(self, value: Any, error: Exception):
        return {
            "kind": "error",
            "error_message": str(error),
            "type": self.value_type(value),
            "value": repr(value),
            "id": id(value),
            "complexity": 0,
        }

    def _visit_complete_failure(
        self, value: Any, original_error: Exception, new_error: Exception
    ):
        return {
            "kind": "complete_failure",
            "error_message": str(original_error),
            "new_error_message": str(new_error),
            "id": id(value),
            "type": "?",
            "complexity": 0,
        }

    def _visit_primitive(self, value: str | int | float | bool | None):
        display_value = (
            repr(value)
            if isinstance(value, (str, bool, int, float, bytes, complex))
            else value
        )
        return {
            "kind": "primitive",
            "value": display_value,
            "type": type(value).__name__,
            "id": id(value),
            "complexity": 1,
        }

    def _visit_cycle(self, value: Any):
        return {
            "kind": "cycle_reference",
            "type": self.value_type(value),
            "targetId": id(value),
            "complexity": 100,
        }

    def _visit_past_max_depth(self, value: Any):
        return {
            "kind": "max_depth_reached",
            "type": self.value_type(value),
            "id": id(value),
            "complexity": 1,
        }

    def _visit_class_instance(
        self, value: Any, is_a_dataclass: bool, depth: int, seen_ids: set[int]
    ):
        rows: list[dict[str, Any]] = []
        total_complexity = 0
        for f in fields(value):
            row = self._walk(getattr(value, f.name), depth + 1, seen_ids)
            rows.append({"name": f.name, "value": row})
            total_complexity += row.get("complexity", 0)

        return {
            "kind": "dataclass" if is_a_dataclass else "class",
            "type": value.__class__.__name__,
            "id": id(value),
            "fields": rows,
            "complexity": 10 + total_complexity,
        }

    def _visit_unknown(self, value: Any):
        return {
            "kind": "unknown",
            "type": self.value_type(value),
            "value": repr(value),
            "id": id(value),
            "complexity": 1,
        }

    def _walk(self, value: Any, depth: int, seen_ids: set[int]) -> dict[str, Any]:
        # Prevent infinite recursion on cyclic refs
        obj_id = id(value)

        if obj_id in seen_ids:
            return self._visit_cycle(value)

        new_seen_ids = seen_ids | {obj_id}

        # Primitive Types
        if isinstance(value, (str, int, float, bool, type(None))):
            return self._visit_primitive(value)

        # Stop at max depth
        if depth > self.max_depth:
            return self._visit_past_max_depth(value)

        # Dataclass expansion
        if is_dataclass(value):
            return self._visit_class_instance(value, True, depth, new_seen_ids)

        # Tuple expansion
        if isinstance(value, tuple):
            return self._visit_tuple(value, depth, new_seen_ids)

        # List/Set expansion
        if isinstance(value, (list, set, frozenset)):
            return self._visit_linear_collection(value, depth, new_seen_ids)

        # Dict expansion
        if isinstance(value, dict):
            return self._visit_dict(value, depth, new_seen_ids)

        # Pillow image
        if HAS_PILLOW and isinstance(value, PILImage.Image):
            return self._visit_pillow_image(value)

        # Primitive or other object: record leaf
        return self._visit_unknown(value)

    def _visit_pillow_image(self, value: PILImage.Image):
        return {
            "kind": "pillow_image",
            "type": self.value_type(value),
            "id": id(value),
            "complexity": 1,
            "value": getattr(value, "filename", None),
        }

    def _visit_tuple(
        self, value: Any, depth: int, seen_ids: set[int]
    ) -> dict[str, Any]:
        rows: list[dict[str, Any]] = []
        types: list[str] = []
        total_complexity = 0
        for index, item in enumerate(value):
            child_row = self._walk(item, depth + 1, seen_ids)
            types.append(child_row.get("fullType", child_row.get("type", "unknown")))
            rows.append(child_row)
            total_complexity += child_row.get("complexity", 0)
        if not types:
            return {
                "kind": "empty_tuple",
                "type": self.value_type(value),
                "id": id(value),
                "complexity": 10 + total_complexity,
            }
        else:
            return {
                "kind": "tuple",
                "type": "tuple",
                "fullType": f"tuple[{', '.join(types)}]",
                "elements": rows,
                "id": id(value),
                "complexity": 10 + total_complexity,
            }

    def _visit_linear_collection(
        self, value: Any, depth: int, seen_ids: set[int]
    ) -> dict[str, Any]:
        rows: list[dict[str, Any]] = []
        type_flattener = TypeFlattener()
        maximum_complexity = 0
        for index, item in enumerate(value):
            child_row = self._walk(item, depth + 1, seen_ids)
            type_flattener.add_type(child_row)
            rows.append(child_row)
            maximum_complexity = max(maximum_complexity, child_row.get("complexity", 0))
        element_kind, element_type = type_flattener.flatten()
        if element_kind == "none":
            return {
                "kind": "empty_linear_collection",
                "type": self.value_type(value),
                "id": id(value),
                "complexity": 10 + maximum_complexity,
            }
        elif element_kind == "homogenous":
            if element_type[0].startswith("list["):
                return {
                    "kind": "homogenous_grid",
                    "type": "list",
                    "elementType": element_type[0],
                    "rows": rows,
                    "fullType": f"list[{element_type[0]}]",
                    "id": id(value),
                    "complexity": 20 + maximum_complexity,
                }
            return {
                "kind": "homogenous_linear_collection",
                "type": self.value_type(value),
                "elementType": element_type[0],
                "fullType": f"{self.value_type(value)}[{element_type[0]}]",
                "elements": rows,
                "id": id(value),
                "complexity": 10 + maximum_complexity,
            }
        elif element_kind == "union":
            flat_type = " | ".join(element_type)
            return {
                "kind": "linear_collection",
                "type": self.value_type(value),
                "elementType": flat_type,
                "fullType": f"{self.value_type(value)}[{flat_type}]",
                "elements": rows,
                "id": id(value),
                "complexity": 10 + maximum_complexity,
            }
        else:
            return self._visit_unknown(value)

    def _visit_dict(self, value: Any, depth: int, seen_ids: set[int]) -> dict[str, Any]:
        rows: list[dict[str, Any]] = []
        key_type_flattener = TypeFlattener()
        value_type_flattener = TypeFlattener()
        maximum_complexity = 0
        for key, val in value.items():
            child_key_row = self._walk(key, depth + 1, seen_ids)
            child_value_row = self._walk(val, depth + 1, seen_ids)
            key_type_flattener.add_type(child_key_row)
            value_type_flattener.add_type(child_value_row)
            maximum_complexity = max(
                maximum_complexity,
                child_key_row.get("complexity", 0),
                child_value_row.get("complexity", 0),
            )
            rows.append(
                {
                    "key": child_key_row,
                    "value": child_value_row,
                }
            )
        key_kind, key_types = key_type_flattener.flatten()
        value_kind, value_types = value_type_flattener.flatten()
        if not rows:
            return {
                "kind": "empty_dict",
                "type": self.value_type(value),
                "id": id(value),
                "complexity": 20 + maximum_complexity,
            }
        else:
            flat_keys, flat_values = " | ".join(key_types), " | ".join(value_types)
            return {
                "kind": "dict",
                "type": self.value_type(value),
                "areKeysHomogenous": key_kind == "homogenous",
                "areValuesHomogenous": value_kind == "homogenous",
                "keyType": flat_keys,
                "valueType": flat_values,
                "fullType": f"dict[{flat_keys}, {flat_values}]",
                "entries": rows,
                "id": id(value),
                "complexity": 20 + maximum_complexity,
            }


def analyze_type(value: Any, max_depth: int = 5) -> dict[str, Any]:
    """Describe a value as a nested representation dict.

    Convenience wrapper around `RecursiveTypeDescriber.analyze`.

    Args:
        value: The Python value to describe.
        max_depth: Maximum recursion depth before traversal stops.

    Returns:
        A representation dict describing `value`, with at least `kind`,
        `type`, and `complexity` fields plus kind-specific children (see
        the module docstring and `RecursiveTypeDescriber.analyze`).
    """
    return RecursiveTypeDescriber(max_depth=max_depth).analyze(value)
