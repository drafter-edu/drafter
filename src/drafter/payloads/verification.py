"""Validation helpers for route return values.

These functions produce `VerificationFailure` records when a route returns
something other than a proper `Page` payload (None, a string, a list, or an
unrelated object), when two components share a name, or when the state
object's type changes from one request to the next. Each failure carries
both the technically concise message and a student-friendly explanation
with concrete fix suggestions, so the error page never has to fall back to
generic debugging advice for these mistakes.
"""

from typing import Any

from drafter.data.request import Request
from drafter.payloads.failure import VerificationFailure
from drafter.payloads.payloads import ResponsePayload


def verify_response_payload_type(
    request: Request, payload: ResponsePayload
) -> VerificationFailure | None:
    """Validate that a payload is a ResponsePayload instance.

    If the payload is None, a string, list, or non-ResponsePayload type,
    returns a failure describing the problem. Otherwise returns None.

    Args:
        request: Associated request providing context (URL).
        payload: Object to validate as a ResponsePayload.

    Returns:
        VerificationFailure or None: Failure record if invalid, None if valid.
    """
    original_function = request.url
    title = "Route Did Not Return a Page"
    if payload is None:
        return VerificationFailure(
            f"The server did not return a Page() object from {original_function}.\n"
            f"Instead, it returned None (which happens by default when you do not return anything else).\n"
            f"Make sure you have a proper return statement for every branch!",
            friendly_title=title,
            friendly_message=(
                f"Your route function `{original_function}` finished without "
                "returning a Page. In Python, a function that does not reach "
                "a return statement gives back None."
            ),
            friendly_steps=(
                "Add a return statement that returns a Page, like "
                "return Page(state, ['Hello!']).",
                "Check every branch of your if/elif/else statements — "
                "each path through the function needs its own return.",
            ),
        )
    elif isinstance(payload, str):
        return VerificationFailure(
            f"The server did not return a Page() object from {original_function}. Instead, it returned a string:\n"
            f"  {payload!r}\n"
            f"Make sure you are returning a Page object with the new state and a list of strings!",
            friendly_title=title,
            friendly_message=(
                f"Your route function `{original_function}` returned a plain "
                "string of text instead of a Page."
            ),
            friendly_steps=(
                "Wrap the text in a Page with a list, like "
                "return Page(state, ['your text here']).",
            ),
        )
    elif isinstance(payload, list):
        return VerificationFailure(
            f"The server did not return a Page() object from {original_function}. Instead, it returned a list:\n"
            f" {payload!r}\n"
            f"Make sure you return a Page object with the new state and the list of strings, not just the list of strings.",
            friendly_title=title,
            friendly_message=(
                f"Your route function `{original_function}` returned a list "
                "of content by itself, instead of putting that list inside "
                "a Page."
            ),
            friendly_steps=(
                "Wrap the list in a Page, like return Page(state, your_list).",
            ),
        )
    elif not isinstance(payload, ResponsePayload):
        return VerificationFailure(
            f"The server did not return a Page() object from {original_function}. Instead, it returned:\n"
            f" {payload!r}\n"
            f"Make sure you return a Page object with the new state and the list of strings.",
            friendly_title=title,
            friendly_message=(
                f"Your route function `{original_function}` returned a "
                f"{type(payload).__name__} instead of a Page."
            ),
            friendly_steps=(
                "Every route function must return a Page, like "
                "return Page(state, ['Hello!']).",
            ),
        )

    return None


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


def verify_unique_component_names(
    request: Request, content: Any
) -> VerificationFailure | None:
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
        VerificationFailure or None: Failure naming the duplicates, None if valid.
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
    duplicate_names = ", ".join(f"`{name}`" for name in duplicates)
    return VerificationFailure(
        f"The page returned from {request.url} has multiple components with "
        f"the same name{plural}:\n" + "\n".join(descriptions) + "\n"
        "Each component must have a unique name, because the name is how "
        "values are matched to route parameters. Rename the duplicates.",
        friendly_title="Components Share a Name",
        friendly_message=(
            f"Two or more components on the page returned from "
            f"`{request.url}` use the same name ({duplicate_names}). Drafter "
            "uses each component's name to match its value to a parameter of "
            "the next route function, so every component needs its own name."
        ),
        friendly_steps=(
            "Rename the components listed above so each has a unique name.",
            "If you want a group of checkboxes that submit together under "
            "one name, use RelatedCheckBox, which is designed to share.",
        ),
    )


def verify_page_state_history(
    request: Request, updated_state: Any, state_history: list
) -> VerificationFailure | None:
    """Validate state type consistency with previous state history.

    Ensures the new state object has the same type as the most recent
    state in the history. Returns a failure if the types don't match.

    Args:
        request: Associated request providing context (URL).
        updated_state: New state value to verify.
        state_history: List of previous state objects.

    Returns:
        VerificationFailure or None: Failure if type mismatch, None if valid.
    """
    original_function = request.url
    if not state_history:
        return None  # No history to compare against
    last_type = state_history[-1].__class__
    if not isinstance(updated_state, last_type):
        return VerificationFailure(
            f"The server did not return a valid Page() object from {original_function}. The state object's type changed from its previous type. The new value is:\n"
            f" {updated_state!r}\n"
            f"The most recent value was:\n"
            f" {state_history[-1]!r}\n"
            f"The expected type was:\n"
            f" {last_type}\n"
            f"Make sure you return the same type each time.",
            friendly_title="State Changed Type",
            friendly_message=(
                f"The page returned from `{original_function}` has a state "
                f"that is a {type(updated_state).__name__}, but the previous "
                f"state was a {last_type.__name__}. The state must stay the "
                "same type from page to page."
            ),
            friendly_steps=(
                "Return the same kind of state object from every route.",
                "If you meant to change one part of the state, update that "
                "field on the existing state instead of returning a "
                "different kind of value.",
            ),
        )
    return None
