"""Tests for the development server's file listing endpoint.

The debug panel's Host File System list (js/src/debug/panels/files.tsx)
asks the local development server which files sit in the student's project
folder, through the reserved `__drafter_list_files` path
(app_server.list_user_files). These tests pin the JSON shape that the
browser side reads (`entries`, each with `name` and `is_dir`) and the
refusals it turns into "no listing". The browser half is covered by
js/src/__tests__/debug-files-panel.test.tsx. The handler is driven directly
(no httpx/TestClient in the test environment).
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

LIST_PATH = "/" + INTERNAL_ROUTES["LIST_FILES"]


def make_system(tmp_path) -> SystemConfiguration:
    project = tmp_path / "project"
    (project / "images").mkdir(parents=True, exist_ok=True)
    (project / "main.py").write_text("print('hello')\n", encoding="utf-8")
    (project / "scores.txt").write_text("1\n", encoding="utf-8")
    (project / "images" / "ada.png").write_bytes(b"png")
    # Next to the project, never inside it.
    (tmp_path / "private.txt").write_text("secret\n", encoding="utf-8")
    app_common = AppCommonConfiguration()
    app_common.prerender_initial_page = False
    system = SystemConfiguration(
        bootstrap=BootstrapConfiguration(path=str(project / "main.py")),
        client_server=ClientServerConfiguration(),
        app_server=AppServerConfiguration(),
        app_builder=AppBuilderConfiguration(),
        app_common=app_common,
    )
    system.app_server.use_reloader = False
    system.app_server.open_browser = False
    return system


def list_files(app, path: str | None = None):
    """Drive the listing handler the way a GET to the endpoint would."""
    query = {} if path is None else {"path": path}
    request = types.SimpleNamespace(app=app, query_params=query)
    response = asyncio.run(app_server.list_user_files(request))
    return response.status_code, json.loads(response.body)


def list_routes(app) -> list[Route]:
    return [
        route
        for route in app.routes
        if isinstance(route, Route) and route.path == LIST_PATH
    ]


class TestListFilesEndpoint:
    def test_lists_the_project_folder_with_folder_flags(self, tmp_path):
        app = app_server.make_app(make_system(tmp_path), MagicMock(), None)

        status, body = list_files(app)

        assert status == 200
        assert sorted(
            (entry["name"], entry["is_dir"]) for entry in body["entries"]
        ) == [("images", True), ("main.py", False), ("scores.txt", False)]

    def test_path_lists_a_subfolder(self, tmp_path):
        app = app_server.make_app(make_system(tmp_path), MagicMock(), None)

        status, body = list_files(app, "images")

        assert status == 200
        assert body["entries"] == [{"name": "ada.png", "is_dir": False}]

    def test_a_file_or_missing_folder_is_refused(self, tmp_path):
        app = app_server.make_app(make_system(tmp_path), MagicMock(), None)

        assert list_files(app, "main.py")[0] == 400
        assert list_files(app, "no-such-folder")[0] == 400

    def test_the_folder_above_the_project_is_refused(self, tmp_path):
        app = app_server.make_app(make_system(tmp_path), MagicMock(), None)

        status, body = list_files(app, "..")

        assert status == 400
        assert "entries" not in body

    def test_route_is_served_only_while_adjacent_files_are(self, tmp_path):
        # With serve_adjacent_files off, the route is not registered; the
        # browser then gets no listing and says so.
        shared = make_system(tmp_path)
        assert len(list_routes(app_server.make_app(shared, MagicMock(), None))) == 1

        private = make_system(tmp_path)
        private.app_server.serve_adjacent_files = False
        assert list_routes(app_server.make_app(private, MagicMock(), None)) == []
