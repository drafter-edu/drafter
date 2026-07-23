"""Default "--reload" route, forcing a full browser page reload."""

from drafter.components import Header, Paragraph
from drafter.payloads.kinds.page import Page


def default_reload(state):
    """Default reload route handler. Forces the page to reload.

    Args:
        state: Current application state.

    Returns:
        Page: A placeholder "Reloading..." page whose JavaScript immediately
        triggers a full browser reload via `window.location.reload()`.
    """
    return Page(
        state,
        [
            Header("Reloading..."),
            Paragraph("The page is reloading. Please wait..."),
        ],
        js="window.location.reload();",
    )
