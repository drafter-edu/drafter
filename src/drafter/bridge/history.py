import json
import time
import html
import js
from dataclasses import dataclass, field
from typing import Callable, Optional, Any

from drafter.bridge.runtime import RuntimeAdapter
from drafter.constants import SUBMIT_BUTTON_KEY
from drafter.data.response import Response
from drafter.data.request import Request
from drafter.bridge.log import debug_log, console_log


class BrowserHistory:
    runtime: RuntimeAdapter
    
    def __init__(self, runtime: RuntimeAdapter):
        self.runtime = runtime

    def add_to_history(self, request: Request):
        url = request.url
        request_id = request.id
        state = {
            "request_id": request_id,
            "url": url,
            "kwargs": json.dumps(request.kwargs) if request.kwargs else "{}",
            # TODO: Track parameters as well
        }
        full_url = self.runtime.create_url(js.location.href)
        # js.document.title = f"{self.site_title} - {url}"
        full_url.searchParams.set("route", url)
        self.runtime.history_push_state(state, "", full_url.toString())
        debug_log("client.add_to_history", state, request)

    def convert_popstate_to_request(self, event: Any) -> Request:
        debug_log("client.handle_popstate", event)
        if (
            event
            and hasattr(event, "state") # and "state" in event
            and hasattr(event.state, "request_id") # and "request_id" in event.state
            and event.state.request_id is not None
        ):
            request_id = event.state.request_id
            url = event.state.url
            kwargs = json.loads(event.state.kwargs) if hasattr(event.state, "kwargs") and event.state.kwargs else {}
            debug_log("client.handle_popstate_with_state", request_id, url)
            # js.document.title = f"{self.site_title} - {url}"
            full_url = self.runtime.create_url(js.location.href)
            full_url.searchParams.set("route", url)
            self.runtime.history_replace_state(event.state, "", full_url.toString())
            # TODO: Restore the data dictionary
            return Request("back", url, kwargs, {}, "", "")
        else:
            debug_log("client.handle_popstate_no_state_or_request_id", event)
            # js.document.title = self.site_title
            full_url = self.runtime.create_url(js.location.href)
            full_url.searchParams.delete("route")
            self.runtime.history_replace_state({}, "", full_url.toString())
            return Request("back", "index", {}, {}, "", "")
