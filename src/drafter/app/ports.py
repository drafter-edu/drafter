"""Making sure the development server's port is usable before it starts.

Students often run their program again while an earlier run is still
serving on port 8000: a forgotten terminal tab, an editor whose stop button
did not end the process, or a run that hung. Left to itself, uvicorn fails
to bind, prints an operating-system error, and exits while the old run
keeps serving the old program. Instead, `prepare_port` checks the port
first and:

1. If an earlier run of the same file holds it, asks that run to stop
   (through its `__drafter_stop_server` endpoint) and waits for the port.
2. Otherwise, when the port is the default one, moves to the next free
   port and says so.
3. When the port was chosen explicitly, raises a student-facing error that
   names the occupant and how to stop it.
"""

import http.client
import json
import os
import socket
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

from drafter.config.app_server import DEFAULT_PORT
from drafter.config.system import SystemConfiguration
from drafter.config.urls import INTERNAL_ROUTES
from drafter.data.errors import StudentFacingError

PROBE_TIMEOUT_SECONDS = 2.0
"""How long to wait for an occupant to answer the status probe or the stop
request. A hung earlier run never answers, so this bounds the delay."""

STOP_WAIT_SECONDS = 5.0
"""How long to wait for the port to free up after asking an earlier run to
stop."""

PORT_SEARCH_LIMIT = 20
"""How many ports above the default are tried when the default is busy."""

STOP_ROUTE_NAME = "--stop-server"
"""The system route students can open to stop a running server."""


def _connect_host(host: str) -> str:
    """The address to connect to for a server bound to `host`.

    Wildcard binds are reached through the loopback address, and IPv6
    literals need brackets in URLs.
    """
    if host in ("", "0.0.0.0"):
        return "127.0.0.1"
    if host == "::":
        return "[::1]"
    if ":" in host and not host.startswith("["):
        return f"[{host}]"
    return host


def server_url(host: str, port: int, path: str = "") -> str:
    """Build the http URL of a development server bound to `host`:`port`.

    Args:
        host: The configured bind host.
        port: The configured port.
        path: Optional path without a leading slash.

    Returns:
        A URL such as "http://localhost:8000/" or
        "http://localhost:8000/--stop-server".
    """
    return f"http://{_connect_host(host)}:{port}/{path}"


def port_is_free(host: str, port: int) -> bool:
    """Whether a server could bind `host`:`port` right now.

    Resolves the host the way asyncio's server creation does and tries to
    bind every resulting address with a throwaway socket. A name that does
    not resolve counts as free so that uvicorn reports that problem itself.

    Args:
        host: The configured bind host.
        port: The configured port.

    Returns:
        True when every address bound, False when any bind failed.
    """
    try:
        infos = socket.getaddrinfo(
            host or None, port, type=socket.SOCK_STREAM, flags=socket.AI_PASSIVE
        )
    except socket.gaierror:
        return True
    seen: set[Any] = set()
    for family, socktype, proto, _canonname, sockaddr in infos:
        if sockaddr in seen:
            continue
        seen.add(sockaddr)
        try:
            sock = socket.socket(family, socktype, proto)
        except OSError:
            continue
        try:
            # Match asyncio: reuse lingering TIME_WAIT addresses on POSIX
            # (Windows semantics differ, and there the plain bind is the
            # accurate test), and keep IPv6 sockets from claiming IPv4 too.
            if os.name != "nt":
                sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            if family == socket.AF_INET6 and hasattr(socket, "IPV6_V6ONLY"):
                sock.setsockopt(socket.IPPROTO_IPV6, socket.IPV6_V6ONLY, True)
            sock.bind(sockaddr)
        except OSError:
            return False
        finally:
            sock.close()
    return True


def find_free_port(host: str, start: int, limit: int = PORT_SEARCH_LIMIT) -> int | None:
    """Find the first free port at or above `start`.

    Args:
        host: The configured bind host.
        start: The first port to try.
        limit: How many consecutive ports to try.

    Returns:
        The first free port, or None when none of them is free.
    """
    for port in range(start, min(start + limit, 65536)):
        if port_is_free(host, port):
            return port
    return None


def _opener() -> urllib.request.OpenerDirector:
    # Never route a loopback probe through a proxy from the environment.
    return urllib.request.build_opener(urllib.request.ProxyHandler({}))


def probe_drafter_server(
    host: str, port: int, timeout: float = PROBE_TIMEOUT_SECONDS
) -> dict[str, Any] | None:
    """Ask whatever listens on `host`:`port` whether it is a Drafter server.

    Fetches the `__drafter_status` endpoint. Anything other than a timely
    JSON object carrying a "drafter" key (another program, an older
    Drafter, a hung run) counts as not a Drafter server.

    Args:
        host: The configured bind host.
        port: The configured port.
        timeout: Seconds to wait for an answer.

    Returns:
        The status payload (with "drafter", "main_file", and "pid" keys)
        or None.
    """
    url = server_url(host, port, INTERNAL_ROUTES["STATUS"])
    try:
        with _opener().open(url, timeout=timeout) as response:
            if response.status != 200:
                return None
            payload = json.loads(response.read().decode("utf-8"))
    except (OSError, ValueError, http.client.HTTPException):
        return None
    if not isinstance(payload, dict) or "drafter" not in payload:
        return None
    return payload


def request_remote_stop(
    host: str, port: int, timeout: float = PROBE_TIMEOUT_SECONDS
) -> bool:
    """Ask the Drafter server on `host`:`port` to shut down.

    Args:
        host: The configured bind host.
        port: The configured port.
        timeout: Seconds to wait for the acknowledgement.

    Returns:
        True when the server acknowledged the stop request.
    """
    url = server_url(host, port, INTERNAL_ROUTES["STOP_SERVER"])
    request = urllib.request.Request(url, method="POST")
    try:
        with _opener().open(request, timeout=timeout) as response:
            return response.status == 200
    except (OSError, http.client.HTTPException):
        return False


def wait_until_free(host: str, port: int, timeout: float = STOP_WAIT_SECONDS) -> bool:
    """Poll until `host`:`port` can be bound or the timeout passes.

    Args:
        host: The configured bind host.
        port: The configured port.
        timeout: Seconds to keep polling.

    Returns:
        True as soon as the port is free, False when the timeout passes.
    """
    deadline = time.monotonic() + timeout
    while True:
        if port_is_free(host, port):
            return True
        if time.monotonic() >= deadline:
            return False
        time.sleep(0.1)


def _normalize_path(path: Any) -> str:
    return os.path.normcase(os.path.abspath(str(path)))


def _same_file(reported: Any, main_path: Path) -> bool:
    if not isinstance(reported, str) or not reported:
        return False
    return _normalize_path(reported) == _normalize_path(main_path)


def _describe_occupant(status: dict[str, Any] | None) -> str:
    if status is None:
        return "another program (possibly an earlier run of yours that is stuck)"
    main_file = status.get("main_file")
    if isinstance(main_file, str) and main_file:
        return f"another Drafter program ({os.path.basename(main_file)})"
    return "another Drafter program"


def prepare_port(system: SystemConfiguration) -> None:
    """Make sure the configured port can be used, adjusting it if needed.

    Checks the port before uvicorn binds it. When an earlier run of the
    same file still holds the port, that run is asked to stop and the port
    is reused. Otherwise, the default port moves to the next free one (and
    the new address is printed), while an explicitly chosen port raises a
    student-facing error instead of silently moving.

    Args:
        system: The system configuration; `app_server.port` is updated in
            place when a different port is chosen.

    Raises:
        StudentFacingError: If an explicitly chosen port is in use, or no
            free port could be found near the default.
    """
    host = system.app_server.host
    port = system.app_server.port
    if port_is_free(host, port):
        return

    main_path = (
        Path(system.bootstrap.get_user_directory()).resolve()
        / system.bootstrap.get_main_filename()
    )
    status = probe_drafter_server(host, port)
    if status is not None and _same_file(status.get("main_file"), main_path):
        print(
            f"An earlier run of {main_path.name} is still using port {port}. "
            "Stopping it so this run can take over..."
        )
        if request_remote_stop(host, port) and wait_until_free(host, port):
            print("Stopped the earlier run.")
            return
        print("The earlier run did not stop.")

    occupant = _describe_occupant(status)
    stop_url = server_url(host, port, STOP_ROUTE_NAME)
    if port != DEFAULT_PORT:
        raise StudentFacingError(
            f"Port {port} is already in use by {occupant}.",
            title="Port already in use",
            friendly=(
                f"You asked Drafter to use port {port}, but {occupant} is "
                "already using it. Drafter only picks a different port on its "
                "own when you have not chosen one."
            ),
            steps=(
                "Stop the other program: if it is an earlier run of a Drafter "
                f"site, press Ctrl+C in its terminal or open {stop_url} in "
                "your browser.",
                f"Or run your program with a different port, such as --port {port + 1}.",
                "Or leave out the port setting, and Drafter will find a free port for you.",
            ),
        )

    new_port = find_free_port(host, port + 1)
    if new_port is None:
        raise StudentFacingError(
            f"Port {port} and the next {PORT_SEARCH_LIMIT - 1} ports are all in use.",
            title="No free port",
            friendly=(
                f"Port {port} is in use by {occupant}, and Drafter could not "
                "find a free port nearby either."
            ),
            steps=(
                "Close other programs that may be running servers, including "
                "earlier runs of your Drafter site.",
                "Or run your program with a specific free port, such as --port 9000.",
            ),
        )
    print(
        f"Port {port} is in use by {occupant}, so this run will use port "
        f"{new_port} instead: {server_url(host, new_port)}"
    )
    if status is not None:
        print(
            f"To stop the other program, open {stop_url} in your browser or "
            "press Ctrl+C in its terminal."
        )
    system.app_server.port = new_port
