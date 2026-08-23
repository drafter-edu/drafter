"""
Navigation control for the bridge: initiating requests and following redirects.

The NavigationController turns navigation triggers (links, form submissions,
system events, browser back/forward) into Requests, dispatches them through
the installed navigation function, records them in BrowserHistory, and
follows redirect responses with loop detection.
"""

import json
from collections.abc import Callable
from typing import Any

from drafter.bridge.error_handling import report_bridge_error, report_bridge_warning
from drafter.bridge.history import BrowserHistory
from drafter.bridge.log import debug_log
from drafter.bridge.snapshot import deserialize_state_snapshot
from drafter.constants import SUBMIT_BUTTON_KEY
from drafter.data.details.state import UpdatedStateEvent
from drafter.data.request import Request
from drafter.data.response import Response
from drafter.monitor.audit import log_record


class NavigationController:
    """Creates and dispatches Requests for all forms of navigation.

    Holds the navigation function (the bridge's visit callback) and invokes
    it for initial page loads, user navigation, popstate replays, and
    redirects, keeping the BrowserHistory in sync and aborting redirect
    loops.

    Attributes:
        history: The BrowserHistory that mirrors requests into the
            browser's history stack.

        browser_history_enabled: Whether navigation is mirrored into the
            browser's history stack at all (the `browser_history`
            configuration setting). When False — embedded instances such as
            documentation demos, which share their host page's history and
            URL — no entries are pushed, the original entry is not stamped,
            and popstate events are ignored, leaving the browser's back
            button to the host page. The request log and replay features
            are unaffected.

        navigation_func: The callback that performs a visit for a Request
            and returns its Response; None until set_navigation_func is
            called.

        get_app_state: Returns the application's current state; None until
            set_state_accessors is called. Used (with set_app_state) to
            restore history-entry state snapshots on back/forward.

        set_app_state: Replaces the application's current state; None until
            set_state_accessors is called.

        redirect_loop_stack: Reprs of the redirect payloads currently being
            followed, used to detect redirect loops.

        last_request: The most recently dispatched Request, kept so the
            debug menu's "Replay Route" (and state snapshots) can re-invoke
            the current route with the same arguments; None before the
            first request.

        request_log: The most recent Requests keyed by their id (bounded to
            REQUEST_LOG_LIMIT entries), so the debug history's "Revisit"
            button can replay a specific past request. Telemetry only
            carries a repr of a request's kwargs, so replays must come from
            these Python-side Request objects.
    """

    #: Maximum number of Requests retained in request_log for replay.
    REQUEST_LOG_LIMIT = 100

    history: BrowserHistory
    browser_history_enabled: bool = True
    navigation_func: Callable[[Request], Response] | None = None
    redirect_loop_stack: list[str]
    last_request: Request | None
    request_log: dict[int, Request]
    get_app_state: Callable[[], Any] | None
    set_app_state: Callable[[Any], None] | None
    #: True once the owning bridge has been torn down; navigation is then
    #: dropped instead of dispatched (see teardown).
    torn_down: bool = False

    def __init__(self, runtime):
        self.history = BrowserHistory(runtime)
        self.browser_history_enabled = True
        self.redirect_loop_stack = []
        self.navigation_func = None
        self.last_request = None
        self.request_log = {}
        self.get_app_state = None
        self.set_app_state = None
        self.torn_down = False

    def teardown(self) -> None:
        """Stop this controller from dispatching any further navigation.

        A click or form submit collects its form data through a promise
        chain, so the navigation it triggers can land *after* the instance
        has been discarded (reset before a re-run). Dispatching such a stale
        visit would re-pin the dead server as the current one (so the next
        run's routes and start_server attach to it) and re-render the dead
        instance's page into the live root. After teardown, navigate and
        handle_popstate drop their requests instead.
        """
        self.torn_down = True

    def set_navigation_func(self, func: Callable[[Request], Response]) -> None:
        """Install the callback used to perform visits.

        Args:
            func: Callback that takes a Request, performs the visit, and
                returns the resulting Response.
        """
        self.navigation_func = func

    def set_state_accessors(
        self,
        get_app_state: Callable[[], Any],
        set_app_state: Callable[[Any], None],
    ) -> None:
        """Install the application-state accessors used for history time
        travel: the BrowserHistory captures a snapshot of the state into
        each entry it pushes, and handle_popstate restores an entry's
        snapshot before replaying its route.

        Args:
            get_app_state: Returns the application's current state.
            set_app_state: Replaces the application's current state.
        """
        self.get_app_state = get_app_state
        self.set_app_state = set_app_state
        self.history.set_state_provider(get_app_state)

    ### Redirect Handling

    def clear_redirect_stack(self) -> None:
        """Empty the redirect loop-detection stack."""
        self.redirect_loop_stack.clear()

    def handle_redirect(
        self, response: Response, callback: Callable[[Request], Response]
    ) -> None:
        """Follow a redirect payload, aborting deterministically on loops.

        Policy: a redirect loop is a canonical bridge *error* (the app's
        redirect logic is broken), reported through structured telemetry.
        The redirect chain is aborted at the first repeated payload, leaving
        the last successfully rendered page in place.
        """
        if repr(response.payload) in self.redirect_loop_stack:
            report_bridge_error(
                "bridge.redirect_loop_detected",
                "Redirect loop detected; aborting redirect chain",
                "bridge.navigation.handle_redirect",
                "Redirect chain: "
                + " -> ".join(self.redirect_loop_stack)
                + f" -> {repr(response.payload)}",
                route=response.url,
                request_id=response.request_id,
                response_id=response.id,
                phase="navigation",
            )
            return
        debug_log("client.handle_redirect", response)
        self.redirect_loop_stack.append(repr(response.payload))
        target_route, arguments = response.payload.get_redirect()
        new_request = Request(
            "redirect",
            target_route,
            arguments if arguments else {},
            {},
            response.target.to_selector() if response.target else "",
        )
        # TODO: Investigate whether we can use the navigation_func
        callback(new_request)
        self.redirect_loop_stack.pop()

    ### Functions for initiating requests ("navigating")

    def goto(
        self,
        url: str,
        data: dict | None = None,
        action="system",
        dom_id=None,
        button_pressed=None,
        remember=True,
    ):
        """General purpose function for navigating to a new page by creating
        a new request and initiating it.

        Args:
            url: The route to visit.
            data: Keyword arguments for the route (becomes the Request's
                `kwargs`). If it contains the submit-button key, that entry
                is popped and used as `button_pressed` when none was given.
            action: The Request action label (e.g. "system", "link",
                "form"). Defaults to "system".
            dom_id: DOM id of the element that triggered the navigation;
                empty string when None.
            button_pressed: The button that initiated the request. When
                falsy, it is extracted from `data` via the submit-button
                key instead.
            remember: Whether the resulting request should be added to
                the browser history (passed through to `navigate`).

        Returns:
            The Response produced by the navigation function.
        """
        button_pressed = button_pressed or extract_button_pressed(data or {})
        request = Request(
            action,
            url,
            data or {},
            {},
            dom_id or "",
            button_pressed=button_pressed or "",
        )
        return self.navigate(request, remember)

    def do_initial_request(self):
        """Issue the initial "page_load" request for the index route.

        The initial request is not added to the browser history, since the
        browser already has an entry for the page itself; instead the
        startup state is stamped onto that original entry (before the index
        route runs and can mutate it), so backing all the way to the start
        restores the app to how it began. When browser history is disabled,
        the original entry is left completely untouched.

        Returns:
            The Response produced by the navigation function.
        """
        if self.browser_history_enabled:
            self.history.record_initial_state()
        initial_request = Request("page_load", "index", {}, {}, "")
        return self.navigate(initial_request, remember=False)

    def handle_popstate(self, event: Any):
        """Replay a browser back/forward navigation as time travel.

        First restores the entry's state snapshot (the application state as
        it was before the entry's route originally ran), then converts the
        popstate event into a Request via the BrowserHistory and dispatches
        it without adding a new history entry (the browser already moved
        within its stack). Re-running the route against the restored state
        reproduces the original page; entries without a usable snapshot
        fall back to replaying against the current state.

        When browser history is disabled, does nothing: popstate events on
        the shared window then belong to the host page (e.g. a
        documentation site's own navigation), and reacting would hijack
        them.

        Args:
            event: The popstate event from the browser.
        """
        if self.torn_down:
            debug_log("client.popstate_ignored_torn_down")
            return
        if not self.browser_history_enabled:
            debug_log("client.popstate_ignored_history_disabled")
            return
        self._restore_state_from_entry(event)
        request = self.history.convert_popstate_to_request(event)
        self.navigate(request, False)

    def _restore_state_from_entry(self, event: Any) -> None:
        """Restore the application state stored in a popstate entry, if any.

        Silently does nothing when the entry carries no snapshot (an entry
        pushed before a snapshot could be captured, or the browser's
        original entry before record_initial_state ran) or when no state
        accessors are installed. A snapshot that can no longer be rebuilt
        (e.g. the state class changed shape since the entry was pushed)
        reports a bridge warning and leaves the current state in place, so
        the navigation degrades to a plain replay instead of failing.
        """
        entry = getattr(event, "state", None) if event is not None else None
        if entry is None:
            return
        state_json = getattr(entry, "state_json", None)
        if not state_json:
            return
        if self.get_app_state is None or self.set_app_state is None:
            return
        route = getattr(entry, "url", None)
        request_id = getattr(entry, "request_id", None)
        try:
            restored = deserialize_state_snapshot(str(state_json), self.get_app_state())
        except Exception as e:
            report_bridge_warning(
                "bridge.history_state_restore_failed",
                "Could not restore this page's saved state (your code may "
                "have changed since it was visited); showing it with the "
                "current state instead",
                "bridge.navigation.handle_popstate",
                f"Route: {route}",
                exception=e,
                route=route,
                request_id=request_id,
                phase="navigation",
            )
            return
        # Restore BEFORE the route replays: argument preparation reads the
        # current state when invoking the route handler.
        self.set_app_state(restored)
        log_record(
            UpdatedStateEvent.from_state(restored),
            "bridge.navigation.handle_popstate",
            route=route,
            request_id=request_id,
        )
        debug_log("client.restore_history_state", route, request_id)

    def navigate(
        self,
        request: Request,
        remember=True,
    ):
        """Takes a Request and initiates it by invoking the navigation function,
        while also notifying the BrowserHistory.

        Args:
            request: The Request to initiate.
            remember: Whether to add the request to the browser history
                before dispatching it (ignored when browser history is
                disabled).

        Returns:
            The Response produced by the navigation function.

        Raises:
            RuntimeError: If the navigation function has not been set via
                `set_navigation_func`.
        """
        if self.torn_down:
            # A stale request from a discarded instance (e.g. a click whose
            # form-data promise resolved after the reset); see teardown.
            debug_log("client.navigate_ignored_torn_down", request)
            return None
        if self.navigation_func is None:
            raise RuntimeError("Navigation function not set in ClientBridge.")
        debug_log("client.initiate_request", request)
        self._record_request(request)
        if remember and self.browser_history_enabled:
            self.history.add_to_history(request)
        next_visit = self.navigation_func(request)
        return next_visit

    ### Replaying past requests (debug menu "Replay Route" / history "Revisit")

    def _record_request(self, request: Request) -> None:
        """Remember a dispatched request for later replay, evicting the
        oldest entries beyond REQUEST_LOG_LIMIT."""
        self.last_request = request
        self.request_log[request.id] = request
        while len(self.request_log) > self.REQUEST_LOG_LIMIT:
            oldest = next(iter(self.request_log))
            del self.request_log[oldest]

    def replay_last(self):
        """Re-dispatch the most recent request (same route and arguments).

        The replay is not added to the browser history (the browser is
        already on this page). Reports a bridge warning and returns None if
        nothing has been requested yet.

        Returns:
            The Response produced by the navigation function, or None.
        """
        if self.last_request is None:
            report_bridge_error(
                "bridge.replay_without_request",
                "No request has been made yet, so there is nothing to replay",
                "bridge.navigation.replay_last",
                "",
                phase="navigation",
            )
            return None
        return self._replay(self.last_request)

    def replay_by_id(
        self,
        request_id: int,
        fallback_url: str | None = None,
        fallback_kwargs: dict | None = None,
    ):
        """Re-dispatch a specific logged request by its id.

        Args:
            request_id: The id of the Request to replay (from the debug
                history timeline).
            fallback_url: Route to visit when the request is no longer in
                the log (e.g. after a bridge restart emptied it); the
                debug history keeps the url/kwargs from telemetry so the
                Revisit button still works.
            fallback_kwargs: Keyword arguments to use with `fallback_url`.

        Returns:
            The Response produced by the navigation function, or None when
            the request has aged out of the log (or never existed) and no
            fallback was available.
        """
        request = self.request_log.get(request_id)
        if request is None:
            if fallback_url:
                return self.goto(
                    fallback_url,
                    dict(fallback_kwargs or {}),
                    action="link",
                    remember=False,
                )
            report_bridge_error(
                "bridge.replay_unknown_request",
                f"Request {request_id} is no longer available to replay",
                "bridge.navigation.replay_by_id",
                f"Logged request ids: {sorted(self.request_log)}",
                phase="navigation",
            )
            return None
        return self._replay(request)

    def _replay(self, original: Request):
        """Dispatch a fresh copy of a past request.

        A copy (with a new request id) is dispatched rather than the
        original object so telemetry can distinguish the replay, and the
        original action label is preserved because route handling (e.g.
        component contract helpers) can depend on it.
        """
        replayed = Request(
            original.action,
            original.url,
            dict(original.kwargs),
            {},
            original.dom_id,
            button_pressed=original.button_pressed,
        )
        return self.navigate(replayed, remember=False)


def extract_button_pressed(data: dict) -> str:
    """Pop and decode the pressed submit button from form data.

    If the submit-button key is present, its entry is removed from `data`
    (mutating the dict). Multi-value form entries (lists) are unwrapped to
    their first element, and string values are JSON-decoded when possible so
    the original button value round-trips; values that are not valid JSON
    are used as-is.

    Args:
        data: The form data dictionary; its submit-button entry, if any, is
            removed.

    Returns:
        The pressed button's value as a string, or an empty string when no
        submit-button entry was present.
    """
    button_pressed = ""
    if SUBMIT_BUTTON_KEY in data:
        button_value = data.pop(SUBMIT_BUTTON_KEY)
        if isinstance(button_value, list) and button_value:
            button_value = button_value[0]
        if isinstance(button_value, str):
            try:
                button_pressed = json.loads(button_value)
            except (json.JSONDecodeError, TypeError):
                button_pressed = button_value
    return str(button_pressed)
