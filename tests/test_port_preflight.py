"""Tests for the development server's port pre-flight (drafter.app.ports).

Before uvicorn binds, prepare_port checks the configured port. An earlier
run of the same file is asked to stop through its stop endpoint and the
port is reused; otherwise a busy default port moves to the next free one,
while an explicitly chosen busy port raises a student-facing error. The
socket and HTTP helpers are exercised against real local sockets and a
tiny threaded HTTP server; the decision logic is tested with the helpers
patched out.
"""

import asyncio
import json
import socket
import threading
import time
import types
from http.server import BaseHTTPRequestHandler, HTTPServer
from unittest.mock import MagicMock

import pytest

from drafter.app import app_server, ports
from drafter.config.app_builder import AppBuilderConfiguration
from drafter.config.app_common import AppCommonConfiguration
from drafter.config.app_server import DEFAULT_PORT, AppServerConfiguration
from drafter.config.bootstrap import BootstrapConfiguration
from drafter.config.client_server import ClientServerConfiguration
from drafter.config.system import SystemConfiguration
from drafter.config.urls import INTERNAL_ROUTES
from drafter.data.errors import StudentFacingError
from drafter.version import CURRENT_DRAFTER_VERSION

HOST = "127.0.0.1"


def make_system(tmp_path, port: int = DEFAULT_PORT) -> SystemConfiguration:
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
    system.app_server.host = HOST
    system.app_server.port = port
    system.app_server.use_reloader = False
    system.app_server.open_browser = False
    return system


@pytest.fixture
def listening_socket():
    """A real listening socket on an OS-assigned port; yields the port."""
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.bind((HOST, 0))
    sock.listen(1)
    try:
        yield sock, sock.getsockname()[1]
    finally:
        sock.close()


class _StatusHandler(BaseHTTPRequestHandler):
    """Serves a Drafter-like status endpoint and accepts stop requests."""

    status_payload: dict = {}
    stop_requests: list[str] = []

    def log_message(self, *args):
        pass

    def do_GET(self):
        if self.path == "/" + INTERNAL_ROUTES["STATUS"] and self.status_payload:
            body = json.dumps(self.status_payload).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(body)
        else:
            self.send_response(404)
            self.end_headers()

    def do_POST(self):
        self.stop_requests.append(self.path)
        if self.path == "/" + INTERNAL_ROUTES["STOP_SERVER"] and self.status_payload:
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b'{"ok": true}')
        else:
            self.send_response(404)
            self.end_headers()


@pytest.fixture
def http_server():
    """A threaded HTTP server; the factory sets its status payload."""
    servers = []

    def start(status_payload: dict | None):
        handler = type(
            "Handler",
            (_StatusHandler,),
            {"status_payload": status_payload or {}, "stop_requests": []},
        )
        server = HTTPServer((HOST, 0), handler)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        servers.append(server)
        return server.server_address[1], handler

    yield start
    for server in servers:
        server.shutdown()
        server.server_close()


class TestPortIsFree:
    def test_listening_port_is_busy(self, listening_socket):
        _sock, port = listening_socket
        assert ports.port_is_free(HOST, port) is False

    def test_closed_port_is_free(self, listening_socket):
        sock, port = listening_socket
        sock.close()
        assert ports.port_is_free(HOST, port) is True

    def test_unresolvable_host_is_left_to_uvicorn(self):
        assert ports.port_is_free("no-such-host.invalid", 8000) is True

    def test_find_free_port_skips_busy_ports(self, listening_socket):
        _sock, port = listening_socket
        found = ports.find_free_port(HOST, port)
        assert found is not None
        assert found != port
        assert ports.port_is_free(HOST, found)

    def test_find_free_port_gives_up_after_limit(self, listening_socket, monkeypatch):
        monkeypatch.setattr(ports, "port_is_free", lambda host, port: False)
        assert ports.find_free_port(HOST, 8000, limit=3) is None


class TestProbe:
    def test_drafter_server_is_recognized(self, http_server):
        payload = {"drafter": "2.0", "main_file": "C:/x/main.py", "pid": 1}
        port, _handler = http_server(payload)
        assert ports.probe_drafter_server(HOST, port) == payload

    def test_other_program_is_not_drafter(self, http_server):
        port, _handler = http_server(None)
        assert ports.probe_drafter_server(HOST, port) is None

    def test_nothing_listening_is_not_drafter(self, listening_socket):
        sock, port = listening_socket
        sock.close()
        assert ports.probe_drafter_server(HOST, port, timeout=0.5) is None

    def test_hung_server_times_out(self, listening_socket):
        # Accepts connections but never answers: the probe must give up.
        _sock, port = listening_socket
        started = time.monotonic()
        assert ports.probe_drafter_server(HOST, port, timeout=0.3) is None
        assert time.monotonic() - started < 3

    def test_stop_request_is_posted(self, http_server):
        port, handler = http_server({"drafter": "2.0"})
        assert ports.request_remote_stop(HOST, port) is True
        assert handler.stop_requests == ["/" + INTERNAL_ROUTES["STOP_SERVER"]]

    def test_stop_request_failure_is_reported(self, http_server):
        port, _handler = http_server(None)
        assert ports.request_remote_stop(HOST, port) is False

    def test_wait_until_free(self, listening_socket):
        sock, port = listening_socket
        threading.Timer(0.3, sock.close).start()
        assert ports.wait_until_free(HOST, port, timeout=5) is True

    def test_wait_until_free_times_out(self, listening_socket):
        _sock, port = listening_socket
        assert ports.wait_until_free(HOST, port, timeout=0.3) is False


class FakeHelpers:
    """Patch the socket/HTTP helpers so prepare_port's decisions are pure."""

    def __init__(self, monkeypatch, *, busy_ports, status, stop_ok=True, frees=True):
        self.busy_ports = set(busy_ports)
        self.status = status
        self.stop_ok = stop_ok
        self.frees = frees
        self.probed: list[int] = []
        self.stopped: list[int] = []
        monkeypatch.setattr(ports, "port_is_free", self.port_is_free)
        monkeypatch.setattr(ports, "probe_drafter_server", self.probe)
        monkeypatch.setattr(ports, "request_remote_stop", self.stop)
        monkeypatch.setattr(ports, "wait_until_free", self.wait)

    def port_is_free(self, host, port):
        return port not in self.busy_ports

    def probe(self, host, port, timeout=None):
        self.probed.append(port)
        return self.status

    def stop(self, host, port, timeout=None):
        self.stopped.append(port)
        return self.stop_ok

    def wait(self, host, port, timeout=None):
        if self.frees:
            self.busy_ports.discard(port)
        return self.frees


class TestPreparePort:
    def test_free_port_is_left_alone(self, tmp_path, monkeypatch, capsys):
        helpers = FakeHelpers(monkeypatch, busy_ports=[], status=None)
        system = make_system(tmp_path)

        ports.prepare_port(system)

        assert system.app_server.port == DEFAULT_PORT
        assert helpers.probed == []
        assert capsys.readouterr().out == ""

    def test_earlier_run_of_same_file_is_stopped_and_port_kept(
        self, tmp_path, monkeypatch, capsys
    ):
        system = make_system(tmp_path)
        status = {"drafter": "2.0", "main_file": str(tmp_path / "main.py")}
        helpers = FakeHelpers(monkeypatch, busy_ports=[DEFAULT_PORT], status=status)

        ports.prepare_port(system)

        assert helpers.stopped == [DEFAULT_PORT]
        assert system.app_server.port == DEFAULT_PORT
        out = capsys.readouterr().out
        assert "earlier run of main.py" in out
        assert "Stopped the earlier run" in out

    def test_same_file_that_will_not_stop_moves_port(
        self, tmp_path, monkeypatch, capsys
    ):
        system = make_system(tmp_path)
        status = {"drafter": "2.0", "main_file": str(tmp_path / "main.py")}
        FakeHelpers(monkeypatch, busy_ports=[DEFAULT_PORT], status=status, frees=False)

        ports.prepare_port(system)

        assert system.app_server.port == DEFAULT_PORT + 1
        out = capsys.readouterr().out
        assert "did not stop" in out
        assert f"use port {DEFAULT_PORT + 1} instead" in out

    def test_other_drafter_program_moves_port_and_explains(
        self, tmp_path, monkeypatch, capsys
    ):
        system = make_system(tmp_path)
        status = {"drafter": "2.0", "main_file": str(tmp_path / "other.py")}
        helpers = FakeHelpers(
            monkeypatch, busy_ports=[DEFAULT_PORT, DEFAULT_PORT + 1], status=status
        )

        ports.prepare_port(system)

        assert helpers.stopped == []
        assert system.app_server.port == DEFAULT_PORT + 2
        out = capsys.readouterr().out
        assert "another Drafter program (other.py)" in out
        assert f"http://{HOST}:{DEFAULT_PORT}/--stop-server" in out

    def test_unknown_program_moves_port(self, tmp_path, monkeypatch, capsys):
        system = make_system(tmp_path)
        FakeHelpers(monkeypatch, busy_ports=[DEFAULT_PORT], status=None)

        ports.prepare_port(system)

        assert system.app_server.port == DEFAULT_PORT + 1
        out = capsys.readouterr().out
        assert "another program" in out
        assert "--stop-server" not in out

    def test_explicit_port_raises_instead_of_moving(self, tmp_path, monkeypatch):
        system = make_system(tmp_path, port=9100)
        FakeHelpers(monkeypatch, busy_ports=[9100], status=None)

        with pytest.raises(StudentFacingError) as excinfo:
            ports.prepare_port(system)

        assert system.app_server.port == 9100
        assert excinfo.value.friendly_title == "Port already in use"
        assert any("--port 9101" in step for step in excinfo.value.friendly_steps)
        assert any("--stop-server" in step for step in excinfo.value.friendly_steps)

    def test_explicit_port_still_takes_over_same_file(self, tmp_path, monkeypatch):
        system = make_system(tmp_path, port=9100)
        status = {"drafter": "2.0", "main_file": str(tmp_path / "main.py")}
        helpers = FakeHelpers(monkeypatch, busy_ports=[9100], status=status)

        ports.prepare_port(system)

        assert helpers.stopped == [9100]
        assert system.app_server.port == 9100

    def test_no_free_port_nearby_raises(self, tmp_path, monkeypatch):
        system = make_system(tmp_path)
        FakeHelpers(
            monkeypatch,
            busy_ports=range(DEFAULT_PORT, DEFAULT_PORT + ports.PORT_SEARCH_LIMIT + 1),
            status=None,
        )

        with pytest.raises(StudentFacingError) as excinfo:
            ports.prepare_port(system)

        assert excinfo.value.friendly_title == "No free port"


class TestStatusEndpoint:
    def test_reports_version_file_and_pid(self, tmp_path):
        app = app_server.make_app(make_system(tmp_path), MagicMock(), None)
        request = types.SimpleNamespace(app=app)

        response = asyncio.run(app_server.server_status(request))

        payload = json.loads(response.body)
        assert response.status_code == 200
        assert payload["drafter"] == CURRENT_DRAFTER_VERSION
        assert payload["main_file"] == str(app.state.user_path)
        assert isinstance(payload["pid"], int)

    def test_status_path_is_never_a_deep_link(self):
        assert app_server.deep_link_target("/" + INTERNAL_ROUTES["STATUS"]) is None


class TestServeAppOncePreflight:
    def test_port_is_prepared_before_uvicorn_binds(self, tmp_path, monkeypatch):
        system = make_system(tmp_path)
        observed: dict = {}

        def fake_prepare(prepared_system):
            prepared_system.app_server.port = 9321
            observed["prepared"] = True

        class FakeUvicornServer:
            def __init__(self, config):
                observed["uvicorn_port"] = config.port

            async def serve(self):
                pass

        monkeypatch.setattr(app_server, "prepare_port", fake_prepare)
        monkeypatch.setattr(app_server.uvicorn, "Server", FakeUvicornServer)

        app_server.serve_app_once(system, MagicMock(), None)

        assert observed == {"prepared": True, "uvicorn_port": 9321}
