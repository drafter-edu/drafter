"""Tests for the development server's stop endpoint (app_server.stop_server).

The browser asks the local development server to shut down by POSTing to
the reserved __drafter_stop_server path (from the debug panel's "Stop
Server" menu item or the --stop-server page). The endpoint calls whatever
stop callback serve_app_once installed on the application state, which
flips uvicorn's exit flag; without one it reports that stopping is not
available instead of crashing. The handler is driven directly (no
httpx/TestClient in the test environment).
"""

import asyncio
import json
import types
from unittest.mock import MagicMock

from starlette.routing import Route

from drafter.app import app_server
from drafter.config.app_builder import AppBuilderConfiguration
from drafter.config.app_common import AppCommonConfiguration
from drafter.config.app_server import AppServerConfiguration
from drafter.config.bootstrap import BootstrapConfiguration
from drafter.config.client_server import ClientServerConfiguration
from drafter.config.system import SystemConfiguration
from drafter.config.urls import INTERNAL_ROUTES

STOP_PATH = "/" + INTERNAL_ROUTES["STOP_SERVER"]


def make_system(tmp_path) -> SystemConfiguration:
    main = tmp_path / "main.py"
    main.write_text("print('hello')\n", encoding="utf-8")
    app_common = AppCommonConfiguration()
    app_common.prerender_initial_page = False
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


def make_app(tmp_path):
    return app_server.make_app(make_system(tmp_path), MagicMock(), None)


def post_stop(app):
    """Drive the stop handler the way a POST to the endpoint would."""
    request = types.SimpleNamespace(app=app)
    response = asyncio.run(app_server.stop_server(request))
    return response.status_code, json.loads(response.body)


def stop_route(app) -> Route:
    matches = [
        route
        for route in app.routes
        if isinstance(route, Route) and route.path == STOP_PATH
    ]
    assert len(matches) == 1
    return matches[0]


class TestStopServerEndpoint:
    def test_post_calls_the_installed_stop_callback(self, tmp_path, capsys):
        app = make_app(tmp_path)
        app.state.request_stop = MagicMock()

        status, body = post_stop(app)

        assert status == 200
        assert body == {"ok": True}
        app.state.request_stop.assert_called_once_with()
        assert "Stopping the server" in capsys.readouterr().out

    def test_without_a_stop_callback_reports_unavailable(self, tmp_path):
        app = make_app(tmp_path)
        assert app.state.request_stop is None

        status, body = post_stop(app)

        assert status == 503
        assert "cannot be stopped" in body["error"]

    def test_endpoint_is_mounted_for_post_only(self, tmp_path):
        # A stray link or prefetch (GET) must never stop the server.
        route = stop_route(make_app(tmp_path))
        assert route.endpoint is app_server.stop_server
        assert route.methods == {"POST"}

    def test_stop_path_is_never_treated_as_a_deep_link(self):
        assert app_server.deep_link_target(STOP_PATH) is None


class TestServeAppOnceInstallsStop:
    def test_stop_callback_flips_uvicorn_exit_flag(self, tmp_path, monkeypatch):
        system = make_system(tmp_path)
        observed: dict = {}

        class FakeUvicornServer:
            def __init__(self, config):
                self.config = config
                self.should_exit = False

            async def serve(self):
                request_stop = self.config.app.state.request_stop
                observed["installed"] = request_stop is not None
                request_stop()
                observed["should_exit"] = self.should_exit

        monkeypatch.setattr(app_server.uvicorn, "Server", FakeUvicornServer)

        app_server.serve_app_once(system, MagicMock(), None)

        assert observed == {"installed": True, "should_exit": True}
