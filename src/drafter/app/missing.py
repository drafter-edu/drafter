"""
TODO: Handle when the requested URL does not exist.

Also serve any files that are available in the starting folder.
"""


def handle_404(error):
    """
    This is the default handler for HTTP 404 errors. It renders a custom error page
    that displays a message indicating the requested page was not found, and provides
    a link to return to the index page.
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
