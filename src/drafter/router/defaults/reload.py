"""Default "--reload" route, forcing a full browser page reload."""

from drafter.components import Header, Paragraph
from drafter.payloads.kinds.page import Page
from drafter.site.deep_links import ROUTE_QUERY_PARAM

RELOAD_SCRIPT = f"""(function () {{
    var url = new URL(window.location.href);
    url.searchParams.delete("{ROUTE_QUERY_PARAM}");
    window.history.replaceState(window.history.state, "", url.toString());
    window.location.reload();
}})();"""
"""JavaScript run by the reload page. Opening a route puts its name in the
address (`?route=--reload`), and a reloaded site opens whatever route the
address names, so the name is removed first. Left in place, every reload
would open this route again and the site would reload without end."""


def default_reload(state):
    """Default reload route handler. Forces the page to reload.

    Args:
        state: Current application state.

    Returns:
        Page: A placeholder "Reloading..." page whose JavaScript removes
        this route's name from the address and then triggers a full browser
        reload, so the site starts again from its first page.
    """
    return Page(
        state,
        [
            Header("Reloading..."),
            Paragraph("The page is reloading. Please wait..."),
        ],
        js=RELOAD_SCRIPT,
    )
