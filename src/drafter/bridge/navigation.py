import json
import time
import html
from dataclasses import dataclass, field
from typing import Callable, Optional, Any

from drafter.bridge.history import BrowserHistory
from drafter.constants import SUBMIT_BUTTON_KEY
from drafter.data.response import Response
from drafter.data.request import Request
from drafter.bridge.log import debug_log, console_log

class NavigationController:
    history: BrowserHistory
    navigation_func: Optional[Callable[[Request], Response]] = None
    redirect_loop_stack: list[str] = field(default_factory=list)
    
    def __init__(self, runtime):
        self.history = BrowserHistory(runtime)
        self.redirect_loop_stack = []
        self.navigation_func = None
        
    def set_navigation_func(self, func: Callable[[Request], Response]) -> None:
        self.navigation_func = func
    
    ### Redirect Handling
    
    def clear_redirect_stack(self) -> None:
        self.redirect_loop_stack.clear()

    def handle_redirect(
        self, response: Response, callback: Callable[[Request], Response]
    ) -> None:
        if repr(response.payload) in self.redirect_loop_stack:
            # TODO: Raise an error here instead of just logging
            console_log(
                "Redirect loop detected: " + " -> ".join(self.redirect_loop_stack)
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
        data: Optional[dict] = None,
        action="system",
        dom_id=None,
        button_pressed=None,
        remember=True,
    ):
        """
        General purpose function for navigating to a new page by creating
        a new request and initiating it.
        """
        button_pressed = button_pressed or extract_button_pressed(data or {})
        request = Request(action, url, data or {}, {}, dom_id or "",
                          button_pressed=button_pressed or "")
        return self.navigate(request, remember)
    
    def do_initial_request(self):
        initial_request = Request("page_load", "index", {}, {}, "")
        return self.navigate(initial_request, remember=False)
        
    def handle_popstate(self, event: Any):
        request = self.history.convert_popstate_to_request(event)
        self.navigate(request, False)

    def navigate(
        self,
        request: Request,
        remember=True,
    ):
        if self.navigation_func is None:
            raise RuntimeError("Navigation function not set in ClientBridge.")
        debug_log("client.initiate_request", request)
        if remember:
            self.history.add_to_history(request)
        next_visit = self.navigation_func(request)
        return next_visit
    
    
def extract_button_pressed(data: dict) -> str:
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