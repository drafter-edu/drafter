"""Structured paths to locations inside nested values and page content.

A path is a list of `PathItem` steps leading from a root value (a compared
value in the testing machinery, or a page's content in the renderer) to one
nested value inside it. Both the testing assertions and the payload renderer
record locations with this vocabulary so that students see locations phrased
the same way everywhere.

The step kinds fall into two groups:

- Comparison steps, produced by `drafter.testing.assertions`: `index`,
  `key`, `set`, `set_item`, `item`, `keys`, `attributes`, `positional`,
  and `children`. These are phrased by `render_path`.
- Rendering steps, produced by `drafter.payloads.renderer`: `index` (a
  position in a list the user wrote), `component` (a Drafter component,
  named by its class), `label` (a human phrase like ``row index 0``
  supplied by a component via `RenderPlan.semantic_label`), `child` (a
  position in a component's internal plan children), and `tag` (an
  internal HTML tag). These are phrased by `render_student_path` (which
  shows only the steps the user can recognize from their own code) and
  `render_debug_path` (which shows everything).
"""

from dataclasses import dataclass


@dataclass
class PathItem:
    """One step in the path from a root value to a nested value.

    Attributes:
        kind: The kind of step (e.g., `index`, `key`, `set`, `item`,
            `attributes`, `positional`, `keys`, `children` for comparison
            paths; `component`, `label`, `child`, `tag` for rendering
            paths), used by the path renderers to phrase the location.
        name: The label for the step, such as the index, key, or component
            name.
    """

    kind: str
    name: str


def render_path(path: list[PathItem]) -> str:
    """Format a comparison path as a human-readable location phrase.

    Walks the PathItems in order, merging `attributes` and `positional`
    steps with the step that follows them, quoting `key`/`item`/`set`
    names, prefixing `index` steps with the word "index", and joining the
    resulting pieces with spaces.

    Args:
        path: The PathItems leading to the mismatch.

    Returns:
        str: The formatted location phrase.
    """
    message = []
    remaining_parts = path[:]
    while remaining_parts:
        path_item = remaining_parts.pop(0)
        if path_item.kind == "attributes":
            if remaining_parts:
                next_path_item = remaining_parts.pop(0)
                message.append(f"{path_item.name} {next_path_item.name}")
            else:
                message.append(f"{path_item.name}")
        elif path_item.kind == "positional":
            if remaining_parts:
                next_path_item = remaining_parts.pop(0)
                if next_path_item.kind == "keys":
                    message.append(f"{path_item.name}")
                else:
                    message.append(f"{path_item.name} {next_path_item.name}")
            else:
                message.append(f"{path_item.name}")
        elif path_item.kind == "children":
            message.append(f"{path_item.name} children")
        elif path_item.kind == "key":
            message.append(f"'{path_item.name}'")
        elif path_item.kind == "item":
            message.append(f"'{path_item.name}'")
        elif path_item.kind == "set":
            message.append(f"'{path_item.name}'")
        elif path_item.kind == "index":
            message.append(f"index '{path_item.name}'")
        else:
            message.append(f"{path_item.kind} '{path_item.name}'")
    return " ".join(message)


def render_student_path(path: list[PathItem]) -> str:
    """Phrase a rendering path using only steps the user can recognize.

    Shows `component` steps (as "the ClassName"), `label` steps (verbatim,
    e.g. ``row index 0``), and `index` steps into lists the user wrote (as
    "the item at index N"). An `index` step immediately followed by the
    component it selects merges into one piece ("the Table at index 1").
    Internal steps (`tag` and `child`) are omitted; they belong to the
    generated HTML structure, not the user's code.

    Args:
        path: The PathItems leading to the failing value.

    Returns:
        str: A comma-joined location phrase, or "" for an empty/internal-only
        path.
    """
    pieces: list[str] = []
    pending_index: str | None = None
    for path_item in path:
        if path_item.kind == "index":
            if pending_index is not None:
                pieces.append(f"the item at index {pending_index}")
            pending_index = path_item.name
        elif path_item.kind == "component":
            if pending_index is not None:
                pieces.append(f"the {path_item.name} at index {pending_index}")
                pending_index = None
            else:
                pieces.append(f"the {path_item.name}")
        elif path_item.kind == "label":
            if pending_index is not None:
                pieces.append(f"the item at index {pending_index}")
                pending_index = None
            pieces.append(path_item.name)
        # "tag" and "child" steps are internal HTML structure: skipped.
    if pending_index is not None:
        pieces.append(f"the item at index {pending_index}")
    return ", ".join(pieces)


def render_debug_path(path: list[PathItem]) -> str:
    """Format a rendering path with every step, for logs and details.

    Args:
        path: The PathItems leading to the failing value.

    Returns:
        str: All steps joined with " > ", indices bracketed (e.g.
        ``[1] > Table > table > [1] > tbody > [0] > tr > row index 0``).
    """
    parts = []
    for path_item in path:
        if path_item.kind in ("index", "child"):
            parts.append(f"[{path_item.name}]")
        else:
            parts.append(path_item.name)
    return " > ".join(parts)
