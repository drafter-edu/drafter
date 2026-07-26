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

from drafter.bridge.error_handling import report_bridge_error
from drafter.bridge.history import BrowserHistory
from drafter.bridge.log import debug_log
from drafter.constants import SUBMIT_BUTTON_KEY
from drafter.data.request import Request
from drafter.data.response import Response


class NavigationController:
    """Creates and dispatches Requests for all forms of navigation.

    Holds the navigation function (the bridge's visit callback) and invokes
    it for initial page loads, user navigation, popstate replays, and
    redirects, keeping the BrowserHistory in sync and aborting redirect
    loops.

    Attributes:
        history: The BrowserHistory that mirrors requests into the
            browser's history stack.

        navigation_func: The callback that performs a visit for a Request
            and returns its Response; None until set_navigation_func is
            called.

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
    navigation_func: Callable[[Request], Response] | None = None
    redirect_loop_stack: list[str]
    last_request: Request | None
    request_log: dict[int, Request]

    def __init__(self, runtime):
        self.history = BrowserHistory(runtime)
        self.redirect_loop_stack = []
        self.navigation_func = None
        self.last_request = None
        self.request_log = {}

    def set_navigation_func(self, func: Callable[[Request], Response]) -> None:
        """Install the callback used to perform visits.

        Args:
            func: Callback that takes a Request, performs the visit, and
                returns the resulting Response.
        """
        self.navigation_func = func

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
        browser already has an entry for the page itself.

        Returns:
            The Response produced by the navigation function.
        """
        initial_request = Request("page_load", "index", {}, {}, "")
        return self.navigate(initial_request, remember=False)

    def handle_popstate(self, event: Any):
        """Replay a browser back/forward navigation.

        Converts the popstate event into a Request via the BrowserHistory
        and dispatches it without adding a new history entry (the browser
        already moved within its stack).

        Args:
            event: The popstate event from the browser.
        """
        request = self.history.convert_popstate_to_request(event)
        self.navigate(request, False)

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
                before dispatching it.

        Returns:
            The Response produced by the navigation function.

        Raises:
            RuntimeError: If the navigation function has not been set via
                `set_navigation_func`.
        """
        if self.navigation_func is None:
            raise RuntimeError("Navigation function not set in ClientBridge.")
        debug_log("client.initiate_request", request)
        self._record_request(request)
        if remember:
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
