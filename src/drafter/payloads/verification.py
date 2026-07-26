"""Validation helpers for route return values.

These functions produce student-friendly error messages when a route
returns something other than a proper `Page` payload (None, a string, a
list, or an unrelated object), or when the state object's type changes
from one request to the next.
"""

from typing import Any

from drafter.data.request import Request
from drafter.payloads.payloads import ResponsePayload


def verify_response_payload_type(request: Request, payload: ResponsePayload):
    """Validate that a payload is a ResponsePayload instance.

    If the payload is None, a string, list, or non-ResponsePayload type,
    returns a descriptive error message. Otherwise returns None.

    Args:
        request: Associated request providing context (URL).
        payload: Object to validate as a ResponsePayload.

    Returns:
        str or None: Error message if invalid, None if valid.
    """
    original_function = request.url
    message = None
    if payload is None:
        message = (
            f"The server did not return a Page() object from {original_function}.\n"
            f"Instead, it returned None (which happens by default when you do not return anything else).\n"
            f"Make sure you have a proper return statement for every branch!"
        )
    elif isinstance(payload, str):
        message = (
            f"The server did not return a Page() object from {original_function}. Instead, it returned a string:\n"
            f"  {payload!r}\n"
            f"Make sure you are returning a Page object with the new state and a list of strings!"
        )
    elif isinstance(payload, list):
        message = (
            f"The server did not return a Page() object from {original_function}. Instead, it returned a list:\n"
            f" {payload!r}\n"
            f"Make sure you return a Page object with the new state and the list of strings, not just the list of strings."
        )
    elif not isinstance(payload, ResponsePayload):
        message = (
            f"The server did not return a Page() object from {original_function}. Instead, it returned:\n"
            f" {payload!r}\n"
            f"Make sure you return a Page object with the new state and the list of strings."
        )

    return message


def collect_named_components(item: Any, found: list) -> None:
    """Recursively collect (name, component) pairs from page content.

    Walks strings/components/lists, descending into each component's
    content arguments. Links and Buttons are skipped: they intentionally
    share one submit-button name.

    Args:
        item: A content item (component, string, list of items, ...).
        found: Output list of (name, component) pairs, appended in order.
    """
    from drafter.components.links import LinkContent
    from drafter.components.page_content import Component

    if isinstance(item, (list, tuple)):
        for child in item:
            collect_named_components(child, found)
        return
    if not isinstance(item, Component):
        return
    if not isinstance(item, LinkContent):
        name = getattr(item, "name", None)
        if isinstance(name, str) and name:
            found.append((name, item))
    for argument in getattr(item, "ARGUMENTS", []):
        if argument.is_content:
            value = getattr(item, argument.name, argument.default_value)
            collect_named_components(value, found)


def verify_unique_component_names(request: Request, content: Any) -> str | None:
    """Validate that no two components on a page share a form-field name.

    Two components with the same name silently merge into one route
    parameter (as a list), which is almost never what a student intends.
    Components whose class sets `ALLOWS_SHARED_NAME` (like RelatedCheckBox)
    share a name by design and are allowed, as long as every component
    using that name opts in.

    Args:
        request: Associated request providing context (URL).
        content: The page's content list.

    Returns:
        str or None: Error message naming the duplicates, None if valid.
    """
    found: list = []
    collect_named_components(content, found)
    first_seen: dict[str, Any] = {}
    duplicates: dict[str, list] = {}
    for name, component in found:
        if name in first_seen:
            duplicates.setdefault(name, [first_seen[name]]).append(component)
        else:
            first_seen[name] = component
    duplicates = {
        name: components
        for name, components in duplicates.items()
        if not all(
            getattr(component, "ALLOWS_SHARED_NAME", False) for component in components
        )
    }
    if not duplicates:
        return None
    descriptions = []
    for name, components in duplicates.items():
        component_types = ", ".join(type(c).__name__ for c in components)
        descriptions.append(f"  {name!r} is used by: {component_types}")
    plural = "s" if len(duplicates) > 1 else ""
    return (
        f"The page returned from {request.url} has multiple components with "
        f"the same name{plural}:\n" + "\n".join(descriptions) + "\n"
        "Each component must have a unique name, because the name is how "
        "values are matched to route parameters. Rename the duplicates."
    )


def verify_page_state_history(
    request: Request, updated_state: Any, state_history: list
) -> str | None:
    """Validate state type consistency with previous state history.

    Ensures the new state object has the same type as the most recent
    state in the history. Returns an error message if types don't match.

    Args:
        request: Associated request providing context (URL).
        updated_state: New state value to verify.
        state_history: List of previous state objects.

    Returns:
        str or None: Error message if type mismatch, None if valid.
    """
    original_function = request.url
    if not state_history:
        return None  # No history to compare against
    last_type = state_history[-1].__class__
    if not isinstance(updated_state, last_type):
        return (
            f"The server did not return a valid Page() object from {original_function}. The state object's type changed from its previous type. The new value is:\n"
            f" {updated_state!r}\n"
            f"The most recent value was:\n"
            f" {state_history[-1]!r}\n"
            f"The expected type was:\n"
            f" {last_type}\n"
            f"Make sure you return the same type each time."
        )
    return None
