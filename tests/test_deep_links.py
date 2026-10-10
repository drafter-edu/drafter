"""Tests for deep links: opening a site directly on a route such as `--about`.

Three pieces cooperate. The static builder writes a `404.html` that GitHub
Pages serves for unknown paths and that redirects `/repo/--about` into
`/repo/?route=--about`. The development server redirects unknown route-like
paths the same way. The bridge's initial request then honors the `route`
query parameter instead of always opening the index, and stamps that route
onto the browser's original history entry so backing to the start returns
to it.
"""

import asyncio
import sys
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock
from urllib.parse import parse_qs, urlsplit

import pytest

# drafter.bridge requires a browser 'js' module; stub it for unit tests.
if not hasattr(sys.modules.get("js"), "document"):
    sys.modules["js"] = MagicMock()

from drafter.app import app_server
from drafter.bridge.history import BrowserHistory
from drafter.bridge.navigation import NavigationController
from drafter.builder.build import (
    CREATE_404_OPTIONS,
    NOT_FOUND_FILENAME,
    compile_site,
    write_404_page,
)
from drafter.config.app_builder import AppBuilderConfiguration
from drafter.config.app_common import AppCommonConfiguration
from drafter.config.app_server import AppServerConfiguration
from drafter.config.bootstrap import BootstrapConfiguration
from drafter.config.client_server import ClientServerConfiguration
from drafter.config.system import SystemConfiguration
from drafter.config.urls import INTERNAL_ROUTES
from drafter.site.deep_links import (
    DEPLOYED_404_TEMPLATE_HTML,
    ROUTE_QUERY_PARAM,
    build_deep_link_url,
)

# ============================================================================
# Shared pieces: the query-parameter convention and the 404 page
# ============================================================================


class TestBuildDeepLinkUrl:
    def test_route_only(self):
        assert build_deep_link_url("--about") == "/?route=--about"

    def test_preserves_other_query_parameters(self):
        assert build_deep_link_url("guess", "answer=4") == "/?route=guess&answer=4"

    def test_nested_route_is_encoded(self):
        url = build_deep_link_url("shop/cart")
        query = parse_qs(urlsplit(url).query)
        assert query[ROUTE_QUERY_PARAM] == ["shop/cart"]


class TestDeployed404Template:
    def test_redirects_into_the_route_query_parameter(self):
        assert f"?{ROUTE_QUERY_PARAM}=" in DEPLOYED_404_TEMPLATE_HTML
        assert "location" in DEPLOYED_404_TEMPLATE_HTML
        assert "l.replace(target)" in DEPLOYED_404_TEMPLATE_HTML

    def test_keeps_the_project_site_segment(self):
        # GitHub Pages project sites live at /repo/, one segment below the host.
        assert "var pathSegmentsToKeep = 1;" in DEPLOYED_404_TEMPLATE_HTML

    def test_guards_against_redirect_loops(self):
        assert "target !== l.href" in DEPLOYED_404_TEMPLATE_HTML


# ============================================================================
# Static builder: writing 404.html according to create_404
# ============================================================================


class TestWrite404Page:
    def test_options_match_configuration_choices(self):
        assert set(CREATE_404_OPTIONS) == {"always", "never", "if_missing"}
        assert AppBuilderConfiguration().create_404 in CREATE_404_OPTIONS

    def test_if_missing_writes_when_absent(self, tmp_path):
        written = write_404_page(tmp_path, "if_missing")

        assert written == tmp_path / NOT_FOUND_FILENAME
        assert written.read_text(encoding="utf-8") == DEPLOYED_404_TEMPLATE_HTML

    def test_if_missing_keeps_an_existing_page(self, tmp_path):
        existing = tmp_path / NOT_FOUND_FILENAME
        existing.write_text("<p>my own 404</p>", encoding="utf-8")

        assert write_404_page(tmp_path, "if_missing") is None
        assert existing.read_text(encoding="utf-8") == "<p>my own 404</p>"

    def test_always_overwrites(self, tmp_path):
        existing = tmp_path / NOT_FOUND_FILENAME
        existing.write_text("<p>my own 404</p>", encoding="utf-8")

        write_404_page(tmp_path, "always")

        assert existing.read_text(encoding="utf-8") == DEPLOYED_404_TEMPLATE_HTML

    def test_never_writes_nothing(self, tmp_path):
        assert write_404_page(tmp_path, "never") is None
        assert not (tmp_path / NOT_FOUND_FILENAME).exists()

    def test_unknown_option_is_rejected(self, tmp_path):
        with pytest.raises(ValueError, match="create_404"):
            write_404_page(tmp_path, "sometimes")


def make_build_system(tmp_path: Path, create_404: str) -> SystemConfiguration:
    """A compile-mode system whose output and assets both live under tmp_path."""
    main_file = tmp_path / "main.py"
    main_file.write_text("from drafter import *\nstart_server()\n", encoding="utf-8")
    assets = tmp_path / "assets"
    assets.mkdir()
    (assets / "placeholder.txt").write_text("asset", encoding="utf-8")
    return SystemConfiguration(
        bootstrap=BootstrapConfiguration(path=str(main_file), mode="compile_site"),
        client_server=ClientServerConfiguration(),
        app_server=AppServerConfiguration(),
        app_builder=AppBuilderConfiguration(
            output_directory=str(tmp_path / "dist"),
            create_404=create_404,
            pyodide_package_style="cdn",
        ),
        app_common=AppCommonConfiguration(
            prerender_initial_page=False, asset_directory=str(assets)
        ),
    )


def make_build_server() -> MagicMock:
    server = MagicMock()
    server.get_config_setting.return_value = None
    return server


class TestCompileSiteWrites404:
    """`compile_site` honors the builder's create_404 setting (it used to
    accept the option and silently ignore it)."""

    def test_default_build_includes_the_404_page(self, tmp_path):
        system = make_build_system(tmp_path, "if_missing")

        compile_site(system, make_build_server(), None)

        output = tmp_path / "dist"
        assert (output / "index.html").exists()
        not_found = output / NOT_FOUND_FILENAME
        assert not_found.read_text(encoding="utf-8") == DEPLOYED_404_TEMPLATE_HTML

    def test_never_skips_the_404_page(self, tmp_path):
        system = make_build_system(tmp_path, "never")

        compile_site(system, make_build_server(), None)

        assert (tmp_path / "dist" / "index.html").exists()
        assert not (tmp_path / "dist" / NOT_FOUND_FILENAME).exists()


# ============================================================================
# Development server: unknown route-like paths redirect like the 404 page
# ============================================================================


class TestDevServerDeepLinkTarget:
    def test_system_route(self):
        assert app_server.deep_link_target("/--about") == "/?route=--about"

    def test_user_route_with_query(self):
        assert app_server.deep_link_target("/guess", "answer=4") == (
            "/?route=guess&answer=4"
        )

    def test_trailing_slash_is_ignored(self):
        assert app_server.deep_link_target("/--about/") == "/?route=--about"

    def test_file_like_paths_stay_missing(self):
        # Fetches and Pyodide's module probes must see a real 404.
        assert app_server.deep_link_target("/pets.csv") is None
        assert app_server.deep_link_target("/images/missing.png") is None
        assert app_server.deep_link_target("/helpers.py") is None

    def test_root_and_reserved_paths_stay_missing(self):
        assert app_server.deep_link_target("/") is None
        for reserved in INTERNAL_ROUTES.values():
            assert app_server.deep_link_target(f"/{reserved}/anything") is None


def make_request(path: str, query: str = ""):
    """A minimal Starlette request for the given path."""
    from starlette.requests import Request as StarletteRequest

    scope = {
        "type": "http",
        "method": "GET",
        "scheme": "http",
        "server": ("localhost", 8080),
        "path": path,
        "query_string": query.encode("utf-8"),
        "headers": [],
    }
    return StarletteRequest(scope)


class TestDevServerNotFoundHandler:
    def test_route_like_path_redirects(self):
        response = asyncio.run(app_server.not_found(make_request("/--about"), None))

        assert response.status_code == 302
        assert response.headers["location"] == "/?route=--about"

    def test_file_like_path_is_a_plain_404(self):
        response = asyncio.run(app_server.not_found(make_request("/pets.csv"), None))

        assert response.status_code == 404

    def test_handler_is_installed_on_the_app(self, tmp_path):
        main_file = tmp_path / "site.py"
        main_file.write_text(
            "from drafter import *\nstart_server()\n", encoding="utf-8"
        )
        system = SystemConfiguration(
            bootstrap=BootstrapConfiguration(path=str(main_file)),
            client_server=ClientServerConfiguration(),
            app_server=AppServerConfiguration(use_reloader=False),
            app_builder=AppBuilderConfiguration(),
            app_common=AppCommonConfiguration(prerender_initial_page=False),
        )

        app = app_server.make_app(system, MagicMock(), None)

        assert app.exception_handlers[404] is app_server.not_found


# ============================================================================
# Bridge: the initial request opens the deep-linked route
# ============================================================================


class FakeUrl:
    """Just enough of the JS URL object for the bridge: searchParams and toString."""

    def __init__(self, href: str):
        parts = urlsplit(href)
        self.base = parts._replace(query="", fragment="").geturl()
        self.query = {k: v[0] for k, v in parse_qs(parts.query).items()}

    @property
    def searchParams(self):  # mirrors the JS property name
        return self

    def get(self, name: str):
        return self.query.get(name)

    def set(self, name: str, value: str) -> None:
        self.query[name] = value

    def delete(self, name: str) -> None:
        self.query.pop(name, None)

    def toString(self) -> str:  # mirrors the JS method name
        if not self.query:
            return self.base
        return self.base + "?" + "&".join(f"{k}={v}" for k, v in self.query.items())


def make_runtime(href: str) -> MagicMock:
    runtime = MagicMock()
    runtime.context.window.location.href = href
    runtime.create_url.side_effect = FakeUrl
    return runtime


class TestInitialRouteFromUrl:
    def test_reads_the_route_parameter(self):
        history = BrowserHistory(make_runtime("http://localhost/?route=--about"))
        assert history.initial_route_from_url() == "--about"

    def test_none_without_the_parameter(self):
        history = BrowserHistory(make_runtime("http://localhost/"))
        assert history.initial_route_from_url() is None

    def test_none_for_an_empty_parameter(self):
        history = BrowserHistory(make_runtime("http://localhost/?route="))
        assert history.initial_route_from_url() is None


def make_navigator(href: str, enabled: bool = True):
    navigator = NavigationController(make_runtime(href))
    navigator.browser_history_enabled = enabled
    navigator.history.set_state_provider(lambda: {"score": 0})
    dispatched = []

    def navigation_func(request):
        dispatched.append(request)
        return SimpleNamespace(url=request.url)

    navigator.set_navigation_func(navigation_func)
    return navigator, dispatched


class TestInitialRequest:
    def test_deep_link_opens_that_route(self):
        navigator, dispatched = make_navigator("http://localhost/?route=--about")

        navigator.do_initial_request()

        assert len(dispatched) == 1
        assert dispatched[0].action == "page_load"
        assert dispatched[0].url == "--about"

    def test_plain_load_opens_the_index(self):
        navigator, dispatched = make_navigator("http://localhost/")

        navigator.do_initial_request()

        assert dispatched[0].url == "index"

    def test_disabled_history_ignores_the_url(self):
        """Embedded instances share their host page's URL and must not read
        a route meant for someone else."""
        navigator, dispatched = make_navigator(
            "http://localhost/docs/?route=--about", enabled=False
        )

        navigator.do_initial_request()

        assert dispatched[0].url == "index"
        navigator.history.runtime.history_replace_state.assert_not_called()

    def test_deep_link_is_not_pushed_but_stamped(self):
        navigator, _ = make_navigator("http://localhost/?route=--about")

        navigator.do_initial_request()

        runtime = navigator.history.runtime
        runtime.history_push_state.assert_not_called()
        runtime.history_replace_state.assert_called_once()
        entry = runtime.history_replace_state.call_args[0][0]
        assert entry["url"] == "--about"
        assert "state_json" in entry
        assert "request_id" not in entry


class TestBackToTheOriginalEntry:
    def test_original_entry_replays_the_deep_linked_route(self):
        navigator, dispatched = make_navigator("http://localhost/?route=--about")
        navigator.do_initial_request()
        stamped = navigator.history.runtime.history_replace_state.call_args[0][0]

        navigator.handle_popstate(SimpleNamespace(state=SimpleNamespace(**stamped)))

        assert dispatched[-1].action == "back"
        assert dispatched[-1].url == "--about"

    def test_unstamped_original_entry_still_falls_back_to_index(self):
        navigator, dispatched = make_navigator("http://localhost/")

        navigator.handle_popstate(SimpleNamespace(state=None))

        assert dispatched[-1].url == "index"


class TestTeardownClearsTheRoute:
    """A new instance started in the same page (editor re-run, test harness)
    must not deep-link into the dead instance's last route."""

    def test_teardown_strips_the_route_parameter(self):
        navigator, _ = make_navigator("http://localhost/?route=tick&x=1")

        navigator.teardown()

        runtime = navigator.history.runtime
        runtime.history_replace_state.assert_called_once()
        new_url = runtime.history_replace_state.call_args[0][2]
        assert ROUTE_QUERY_PARAM not in parse_qs(urlsplit(new_url).query)
        assert parse_qs(urlsplit(new_url).query) == {"x": ["1"]}

    def test_teardown_leaves_a_clean_url_alone(self):
        navigator, _ = make_navigator("http://localhost/")

        navigator.teardown()

        navigator.history.runtime.history_replace_state.assert_not_called()

    def test_disabled_history_never_touches_the_url(self):
        navigator, _ = make_navigator("http://localhost/docs/?route=x", enabled=False)

        navigator.teardown()

        navigator.history.runtime.history_replace_state.assert_not_called()

    def test_successor_in_the_same_page_starts_at_index(self):
        runtime = make_runtime("http://localhost/?route=tick")
        first = NavigationController(runtime)
        first.set_navigation_func(lambda request: SimpleNamespace(url=request.url))
        first.teardown()
        # The successor sees the URL the teardown left behind.
        runtime.context.window.location.href = runtime.history_replace_state.call_args[
            0
        ][2]
        second = NavigationController(runtime)
        dispatched = []
        second.set_navigation_func(
            lambda request: dispatched.append(request)
            or SimpleNamespace(url=request.url)
        )

        second.do_initial_request()

        assert dispatched[0].url == "index"


async def asgi_get(app, path: str) -> tuple[int, dict[str, str]]:
    """Drive the Starlette app through raw ASGI (no httpx needed)."""
    scope = {
        "type": "http",
        "http_version": "1.1",
        "method": "GET",
        "scheme": "http",
        "server": ("localhost", 8080),
        "client": ("127.0.0.1", 50000),
        "root_path": "",
        "path": path,
        "raw_path": path.encode("utf-8"),
        "query_string": b"",
        "headers": [],
    }
    status = {"code": 0}
    headers: dict[str, str] = {}

    async def receive():
        return {"type": "http.request", "body": b"", "more_body": False}

    async def send(message):
        if message["type"] == "http.response.start":
            status["code"] = message["status"]
            for name, value in message["headers"]:
                headers[name.decode("latin-1")] = value.decode("latin-1")

    await app(scope, receive, send)
    return status["code"], headers


class TestDevServerThroughAsgi:
    """The 404 handler must catch misses from the user-files mount, not only
    unmatched routes, since the user directory is mounted at the root."""

    def make_app(self, tmp_path):
        main_file = tmp_path / "site.py"
        main_file.write_text(
            "from drafter import *\nstart_server()\n", encoding="utf-8"
        )
        system = SystemConfiguration(
            bootstrap=BootstrapConfiguration(path=str(main_file)),
            client_server=ClientServerConfiguration(),
            app_server=AppServerConfiguration(use_reloader=False),
            app_builder=AppBuilderConfiguration(),
            app_common=AppCommonConfiguration(prerender_initial_page=False),
        )
        return app_server.make_app(system, MagicMock(), None)

    def test_about_path_redirects_into_the_index(self, tmp_path):
        app = self.make_app(tmp_path)

        status, headers = asyncio.run(asgi_get(app, "/--about"))

        assert status == 302
        assert headers["location"] == "/?route=--about"

    def test_missing_file_stays_404(self, tmp_path):
        app = self.make_app(tmp_path)

        status, _ = asyncio.run(asgi_get(app, "/missing.csv"))

        assert status == 404

    def test_existing_file_is_still_served(self, tmp_path):
        (tmp_path / "pets.csv").write_text("name\nAda\n", encoding="utf-8")
        app = self.make_app(tmp_path)

        status, _ = asyncio.run(asgi_get(app, "/pets.csv"))

        assert status == 200
