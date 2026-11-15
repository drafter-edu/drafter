"""Tests for the default reload page (router/defaults/reload.py).

Opening a route puts its name in the address bar as `?route=<name>`, and a
reloaded site opens the route named there. The reload page therefore has to
take its own name out of the address before reloading, or the site reloads
forever. js/e2e/deep-link.spec.ts checks the same thing in a real browser.
"""

from drafter.payloads.kinds.page import Page
from drafter.router.defaults.reload import default_reload
from drafter.router.system_routes import _SYSTEM_ROUTES
from drafter.site.deep_links import ROUTE_QUERY_PARAM


class TestDefaultReload:
    def test_registered_as_system_route(self):
        assert _SYSTEM_ROUTES["--reload"] is default_reload

    def test_returns_page_with_state(self):
        page = default_reload("state")

        assert isinstance(page, Page)
        assert page.state == "state"

    def test_route_name_leaves_the_address_before_the_reload(self):
        script = default_reload("state").js

        remove_route = f'searchParams.delete("{ROUTE_QUERY_PARAM}")'
        assert remove_route in script
        assert "history.replaceState" in script
        assert script.index(remove_route) < script.index("history.replaceState")
        assert script.index("history.replaceState") < script.index("location.reload()")
