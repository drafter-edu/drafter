"""Tests that a browser cannot pair a page with a stale Drafter bundle.

Regression: after upgrading Drafter, a browser could keep using the
`drafter.pyodide.js` it had cached from the previous version, because the
development server served it from the same URL with no `Cache-Control`
header (so the browser guessed it was still fresh). The new page pointed at
a newer Pyodide than the cached bundle's loader understood, and the site
died with "Failed to fetch dynamically imported module: .../pyodide.asm.js".

Two things prevent that now: the index page's asset URLs carry the Drafter
version, and the development server tells browsers to revalidate Drafter's
assets before reusing them. The static-file app is driven directly (no
httpx/TestClient in the test environment).
"""

import asyncio
import re
from pathlib import Path
from unittest.mock import MagicMock

import pytest
from starlette.applications import Starlette
from starlette.responses import Response
from starlette.routing import Mount
from starlette.staticfiles import StaticFiles
from starlette.types import ASGIApp

from drafter.app import app_server
from drafter.config.app_builder import AppBuilderConfiguration
from drafter.config.app_common import AppCommonConfiguration
from drafter.config.app_server import AppServerConfiguration
from drafter.config.bootstrap import BootstrapConfiguration
from drafter.config.client_server import ClientServerConfiguration
from drafter.config.system import SystemConfiguration
from drafter.config.urls import INTERNAL_ROUTES
from drafter.scaffolding import templating
from drafter.version import CURRENT_DRAFTER_VERSION

ASSETS_PATH = "/" + INTERNAL_ROUTES["ASSETS"]
BUNDLE = "js/drafter.pyodide.js"


def make_system(tmp_path: Path) -> SystemConfiguration:
    main = tmp_path / "main.py"
    main.write_text("print('hello')\n", encoding="utf-8")
    assets = tmp_path / "assets"
    (assets / "js").mkdir(parents=True)
    (assets / BUNDLE).write_text("console.log('bundle');\n", encoding="utf-8")
    app_common = AppCommonConfiguration()
    app_common.prerender_initial_page = False
    app_common.asset_directory = str(assets)
    system = SystemConfiguration(
        bootstrap=BootstrapConfiguration(path=str(main)),
        client_server=ClientServerConfiguration(),
        app_server=AppServerConfiguration(),
        app_builder=AppBuilderConfiguration(),
        app_common=app_common,
    )
    system.app_server.use_reloader = False
    system.app_server.open_browser = False
    return system


def render_index(system: SystemConfiguration) -> str:
    return templating.render_index_html(
        system=system,
        modified_system={},
        inline_py=True,
        user_code="",
        python_url=None,
        dev_ws_url=None,
        assets_url=ASSETS_PATH,
    )


def bundle_script_src(html: str) -> str:
    sources = re.findall(r'<script src="([^"]*drafter\.pyodide\.js[^"]*)"', html)
    assert len(sources) == 1
    return sources[0]


def mounted_app(app: Starlette, mount_path: str) -> ASGIApp:
    matches = [
        route
        for route in app.routes
        if isinstance(route, Mount) and route.path == mount_path
    ]
    assert len(matches) == 1
    return matches[0].app


def get_asset(
    app: Starlette, path: str, headers: dict[str, str] | None = None
) -> Response:
    """Ask the assets mount for a file the way a browser GET would."""
    static_files = mounted_app(app, ASSETS_PATH)
    assert isinstance(static_files, StaticFiles)
    scope = {
        "type": "http",
        "method": "GET",
        "headers": [
            (name.lower().encode("latin-1"), value.encode("latin-1"))
            for name, value in (headers or {}).items()
        ],
    }
    return asyncio.run(static_files.get_response(path, scope))


class TestVersionedAssetUrls:
    def test_bundle_url_carries_the_drafter_version(self, tmp_path):
        src = bundle_script_src(render_index(make_system(tmp_path)))
        assert src == f"{ASSETS_PATH}/{BUNDLE}?v={CURRENT_DRAFTER_VERSION}"

    def test_bundle_url_changes_when_drafter_is_upgraded(
        self, tmp_path, monkeypatch: pytest.MonkeyPatch
    ):
        system = make_system(tmp_path)
        monkeypatch.setattr(templating, "CURRENT_DRAFTER_VERSION", "2.0.3")
        before_upgrade = bundle_script_src(render_index(system))
        monkeypatch.setattr(templating, "CURRENT_DRAFTER_VERSION", "2.1.0")
        after_upgrade = bundle_script_src(render_index(system))
        # A different URL is a different browser-cache entry, so the bundle
        # cached before the upgrade can never be used by the new page.
        assert before_upgrade != after_upgrade


class TestDevServerAssetRevalidation:
    def test_asset_responses_must_be_revalidated(self, tmp_path):
        app = app_server.make_app(make_system(tmp_path), MagicMock(), None)

        response = get_asset(app, BUNDLE)

        assert response.status_code == 200
        assert response.headers["cache-control"] == "no-cache"
        # Revalidation needs a validator to compare against.
        assert response.headers["etag"]

    def test_not_modified_responses_keep_requiring_revalidation(self, tmp_path):
        app = app_server.make_app(make_system(tmp_path), MagicMock(), None)
        etag = get_asset(app, BUNDLE).headers["etag"]

        response = get_asset(app, BUNDLE, {"If-None-Match": etag})

        assert response.status_code == 304
        assert response.headers["cache-control"] == "no-cache"

    def test_changed_asset_is_served_again_after_revalidation(self, tmp_path):
        system = make_system(tmp_path)
        app = app_server.make_app(system, MagicMock(), None)
        etag = get_asset(app, BUNDLE).headers["etag"]
        bundle = Path(str(system.app_common.asset_directory)) / BUNDLE
        bundle.write_text("console.log('a newer, longer bundle');\n", encoding="utf-8")

        response = get_asset(app, BUNDLE, {"If-None-Match": etag})

        assert response.status_code == 200
        assert response.headers["etag"] != etag
