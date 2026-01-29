from drafter.components import Header, Paragraph
from drafter.payloads.kinds.page import Page


def default_index(state):
    """Display the default welcome page.

    This is the built-in index route shown when no user-provided index
    exists. Users should create their own index page instead of modifying
    this function.

    Args:
        state: Current application state.

    Returns:
        Page: Simple welcome message.
    """
    return Page(state, [Header("Hello world!"), Paragraph("Welcome to Drafter.")])
