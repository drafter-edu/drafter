"""Deep links: opening a Drafter site directly on a route.

A deployed Drafter site is a single `index.html`; routes exist only inside
the running Pyodide app. A visitor who types `https://user.github.io/repo/--about`
therefore asks the host for a file that does not exist. This module defines
the convention that turns such a path back into a route the app can open:

- The route travels in the `route` query parameter of the index page, the
  same encoding `BrowserHistory` already uses for back/forward entries, so
  `https://user.github.io/repo/?route=--about` opens the About page.
- `DEPLOYED_404_TEMPLATE_HTML` is the `404.html` the static builder writes
  next to `index.html`. GitHub Pages serves it for every missing path, and
  its script rewrites the path into the `route` query form and redirects.
- `build_deep_link_url` produces the same redirect target for the
  development server, so `http://localhost:8080/--about` behaves like the
  deployed site.
"""

from urllib.parse import urlencode

ROUTE_QUERY_PARAM = "route"
"""Name of the query parameter carrying the route a page should open on,
shared by browser-history entries, deep-link redirects, and the 404 page."""

DEPLOYED_404_TEMPLATE_HTML = f"""<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="utf-8">
    <title>Redirecting to the site</title>
    <script>
      // Drafter deep-link redirect for GitHub Pages project sites.
      // GitHub serves this page for any path that is not a real file, such as
      // https://user.github.io/repo/--about. The site itself lives in
      // index.html, so the extra path is handed to it as a query parameter:
      // https://user.github.io/repo/?{ROUTE_QUERY_PARAM}=--about
      (function () {{
        // Project sites live one path segment below the domain (/repo/).
        var pathSegmentsToKeep = 1;
        var l = window.location;
        var segments = l.pathname.split("/");
        var base = segments.slice(0, 1 + pathSegmentsToKeep).join("/") + "/";
        var route = segments.slice(1 + pathSegmentsToKeep).join("/");
        var query = "?{ROUTE_QUERY_PARAM}=" + encodeURIComponent(route);
        if (l.search) {{
          query += "&" + l.search.slice(1);
        }}
        var target = l.protocol + "//" + l.host + base + query + l.hash;
        if (target !== l.href) {{
          l.replace(target);
        }}
      }})();
    </script>
  </head>
  <body>
    <p>Redirecting to the site...</p>
  </body>
</html>
"""
"""Contents of the `404.html` written by the static builder. The script keeps
one path segment (the repository name of a GitHub Pages project site) and
moves the rest of the path into the `route` query parameter of the index
page, preserving any original query string and fragment. It stops instead
of looping when the redirect target is the page it is already on."""


def build_deep_link_url(route: str, query_string: str = "") -> str:
    """Build the index-page URL that opens the site on a route.

    Args:
        route: The route path the visitor asked for, without a leading
            slash (for example `--about` or `guess`).
        query_string: The original query string without its leading `?`,
            appended after the route parameter so other parameters survive.

    Returns:
        A root-relative URL such as `/?route=--about` or
        `/?route=guess&answer=4`.

    Example:
        ```python
        build_deep_link_url("--about")
        # '/?route=--about'
        build_deep_link_url("guess", "answer=4")
        # '/?route=guess&answer=4'
        ```
    """
    url = "/?" + urlencode({ROUTE_QUERY_PARAM: route})
    if query_string:
        url += "&" + query_string
    return url
