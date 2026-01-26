"""HTTP 404 error handling for the development server.

Provides a custom 404 error handler that displays available routes.

TODO:
    Handle when the requested URL does not exist.
    Also serve any files that are available in the starting folder.
"""


def handle_404(error):
    """Handle HTTP 404 errors with custom page.

    Renders a custom 404 error page that displays the requested URL,
    provides a link to the index page, and lists available routes.

    Args:
        error: The HTTP error object.

    Returns:
        Formatted error page HTML (format varies by template).

    TODO:
        This implementation appears incomplete; verify full implementation
        and ensure integration with Drafter's error handling system.
    """
    message = "<p>The requested page <code>{url}</code> was not found.</p>".format(
        url=request.url
    )
    # TODO: Only show if not the index
    message += "\n<p>You might want to return to the <a href='/'>index</a> page.</p>"
    original_error = f"{error.body}\n"
    if hasattr(error, "traceback"):
        original_error += f"{error.traceback}\n"
    return TEMPLATE_404.format(
        title="404 Page not found",
        message=message,
        error=original_error,
        routes="\n".join(
            f"<li><code>{r!r}</code>: <code>{func}</code></li>"
            for r, func in self.original_routes
        ),
    )
