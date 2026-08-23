"""
Browser history integration for the bridge.

Mirrors Drafter's simulated navigation into the browser's history stack (as a
``route`` query parameter plus serialized request state) so the back/forward
buttons work, and converts popstate events back into Requests to replay.

Each entry also carries a JSON snapshot of the application state as it was
*before* the entry's route ran (``navigate`` records history before invoking
the route), so back/forward can restore that state and re-run the route to
reproduce the original page — time travel rather than a replay against
whatever the state has since become. The NavigationController performs the
restore side; this module only captures snapshots into entries.
"""

import json
from collections.abc import Callable
from typing import Any

from drafter.bridge.error_handling import report_bridge_warning
from drafter.bridge.log import debug_log
from drafter.bridge.runtime import RuntimeAdapter
from drafter.bridge.snapshot import encode_state_json
from drafter.data.request import Request


class BrowserHistory:
    """Bridges Drafter navigation and the browser's history stack.

    All history operations go through the RuntimeAdapter (and its DomContext)
    so each instance manipulates the history of the window it actually
    renders into, which may be an iframe rather than the top page.

    Attributes:
        runtime: Adapter providing history push/replace and URL creation for
            this instance's window.

        get_app_state: Callable returning the application's current state,
            injected via set_state_provider; None until then (entries are
            then recorded without state snapshots).
    """

    #: State snapshots longer than this (in JSON characters) are dropped from
    #: history entries rather than bloat the browser's session history;
    #: back/forward then degrades to replaying against the current state.
    MAX_STATE_JSON_LENGTH = 1_000_000

    runtime: RuntimeAdapter
    get_app_state: Callable[[], Any] | None

    def __init__(self, runtime: RuntimeAdapter):
        self.runtime = runtime
        self.get_app_state = None

    def set_state_provider(self, get_app_state: Callable[[], Any]) -> None:
        """Install the callable used to read the application state when
        capturing a snapshot into a history entry.

        Args:
            get_app_state: Returns the application's current state value.
        """
        self.get_app_state = get_app_state

    def _capture_state_json(self, route: str, request_id: int | None) -> str | None:
        """Snapshot the current application state for a history entry.

        Returns:
            The state encoded as snapshot JSON, or None when no state
            provider is installed, the state cannot be reduced to simple
            data, or the snapshot exceeds MAX_STATE_JSON_LENGTH (the latter
            two report a bridge warning; the entry is then recorded without
            a snapshot and back/forward replays against the current state).
        """
        if self.get_app_state is None:
            return None
        try:
            state_json = encode_state_json(self.get_app_state())
        except Exception as e:
            report_bridge_warning(
                "bridge.history_state_serialization_failed",
                "Could not save the current state into browser history; "
                "the back button will show this page with whatever the "
                "state is at that time",
                "bridge.history.add_to_history",
                "",
                exception=e,
                route=route,
                request_id=request_id,
                phase="navigation",
            )
            return None
        if len(state_json) > self.MAX_STATE_JSON_LENGTH:
            report_bridge_warning(
                "bridge.history_state_too_large",
                "The current state is too large to save into browser "
                "history; the back button will show this page with "
                "whatever the state is at that time",
                "bridge.history.add_to_history",
                f"State snapshot length: {len(state_json)} characters "
                f"(limit {self.MAX_STATE_JSON_LENGTH})",
                route=route,
                request_id=request_id,
                phase="navigation",
            )
            return None
        return state_json

    def record_initial_state(self) -> None:
        """Stamp the startup state onto the browser's original history entry.

        The initial page load is never pushed (the browser already has an
        entry for the page itself), so without this, backing all the way to
        the start would replay the index route against the accumulated
        current state. Replacing the original entry's state with a snapshot
        of the just-constructed startup state lets that final "back" restore
        the app to how it began. Does nothing when the state cannot be
        captured.
        """
        state_json = self._capture_state_json("index", None)
        if state_json is None:
            return
        self.runtime.history_replace_state(
            {"state_json": state_json}, "", self._current_href()
        )
        debug_log("client.record_initial_state")

    def _current_href(self) -> str:
        """The href of the window this instance renders into (may be an iframe)."""
        return self.runtime.context.window.location.href

    def add_to_history(self, request: Request):
        """Push a request onto the browser history stack.

        Stores the request's id, route, and JSON-serialized kwargs as the
        history entry's state, plus a snapshot of the application state as
        it is right now — before the request's route runs (navigate records
        history first) — so back/forward can restore it and reproduce the
        visit. The visible URL is rewritten to carry the route as a
        ``route`` query parameter. If the kwargs cannot be serialized, a
        bridge warning is reported and empty arguments are stored instead;
        an uncapturable state simply omits the snapshot.

        Args:
            request: The request being navigated to.
        """
        url = request.url
        request_id = request.id
        try:
            kwargs = json.dumps(request.kwargs) if request.kwargs else "{}"
        except Exception as e:
            report_bridge_warning(
                "bridge.history_kwargs_serialization_failed",
                "Could not serialize request arguments for browser history; using empty arguments",
                "bridge.history.add_to_history",
                f"Request kwargs: {repr(request.kwargs)}",
                exception=e,
                route=url,
                request_id=request_id,
                phase="navigation",
            )
            kwargs = "{}"
        state = {
            "request_id": request_id,
            "url": url,
            "kwargs": kwargs,
        }
        state_json = self._capture_state_json(url, request_id)
        if state_json is not None:
            state["state_json"] = state_json
        full_url = self.runtime.create_url(self._current_href())
        # js.document.title = f"{self.site_title} - {url}"
        full_url.searchParams.set("route", url)
        self.runtime.history_push_state(state, "", full_url.toString())
        debug_log("client.add_to_history", state, request)

    def convert_popstate_to_request(self, event: Any) -> Request:
        """Turn a browser popstate event into a Request to replay.

        If the event carries state with a request id (i.e. an entry this
        instance pushed), rebuilds a "back" Request for the stored route and
        kwargs and re-syncs the visible URL's ``route`` query parameter via
        replaceState. Otherwise (no usable state, e.g. the original entry),
        strips the ``route`` parameter and falls back to a "back" Request
        for the index route.

        Restoring the entry's state snapshot is not done here: the
        NavigationController restores it before dispatching the returned
        Request (argument preparation reads the current state).

        Args:
            event: The popstate event from the browser.

        Returns:
            A Request with action "back" targeting the restored route, or
            the index route when the event carried no usable state.
        """
        debug_log("client.handle_popstate", event)
        if (
            event
            and hasattr(event, "state")  # and "state" in event
            and hasattr(event.state, "request_id")  # and "request_id" in event.state
            and event.state.request_id is not None
        ):
            request_id = event.state.request_id
            url = event.state.url
            kwargs = (
                json.loads(event.state.kwargs)
                if hasattr(event.state, "kwargs") and event.state.kwargs
                else {}
            )
            debug_log("client.handle_popstate_with_state", request_id, url)
            # js.document.title = f"{self.site_title} - {url}"
            full_url = self.runtime.create_url(self._current_href())
            full_url.searchParams.set("route", url)
            self.runtime.history_replace_state(event.state, "", full_url.toString())
            return Request("back", url, kwargs, {}, "", "")
        else:
            debug_log("client.handle_popstate_no_state_or_request_id", event)
            # js.document.title = self.site_title
            full_url = self.runtime.create_url(self._current_href())
            full_url.searchParams.delete("route")
            self.runtime.history_replace_state({}, "", full_url.toString())
            return Request("back", "index", {}, {}, "", "")
