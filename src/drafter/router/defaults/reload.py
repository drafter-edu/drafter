from drafter.payloads.kinds.page import Page
from drafter.components import Header, Paragraph


def default_reload(state):
    """Default reload route handler. Forces the page to reload.

    Args:
        state: Current application state.

    Returns:
        None: Indicates a page reload.
    """
    return Page(
        state,
        [
            Header("Reloading..."),
            Paragraph("The page is reloading. Please wait..."),
        ],
        js="window.location.reload();",
    )
