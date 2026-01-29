from drafter.client_server.client_server import ClientServer
from drafter.payloads.kinds.page import Page
from drafter.components import Header, Paragraph, PreformattedText, Span, Link
from drafter.monitor.events.errors import DrafterError


def default_error(state, error: DrafterError, server: ClientServer):
    """Default error route handler.

    Args:
        state: Current application state.
        error: The error that occurred.

    Returns:
        Page: Page content with error information.
    """
    content = [
        Header("Error", level=2),
        Paragraph(f"An error has occurred: {type(error).__name__}"),
        Paragraph("Message:"),
        PreformattedText(error.message),
        Paragraph("Details:"),
        PreformattedText(error.details),
        Paragraph("Where:", Span(error.where)),
        Paragraph("Traceback:"),
        PreformattedText(error.traceback or "No traceback available."),
        Paragraph("Navigation options:"),
        Link("Return to Index Page", "index"),
        Link("Reset State and Return to Index", "--reset"),
        Link("Reload Page", "--reload"),
    ]
    # TODO: Consider a hard refresh option that appends a nonce to the URL
    return Page(state, content)
