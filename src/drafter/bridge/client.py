"""
Client bridge module for interacting with the browser DOM using the js package.
This module works with both Skulpt and Pyodide by using the unified js interface.
"""

from drafter.data.response import Response
from drafter.data.request import Request
from drafter.site.site import DRAFTER_TAG_IDS, DRAFTER_TAG_CLASSES
from drafter.monitor.telemetry import TelemetryEvent, TelemetryCorrelation
from drafter.monitor.bus import get_main_event_bus
from typing import Callable, Optional, Any
from dataclasses import dataclass
import js

# Module-level state
_navigation_func: Optional[Callable] = None
_request_count = 1
_site_title = ""
_debug_panel: Optional[Any] = None
_click_handler: Optional[Any] = None
_submit_handler: Optional[Any] = None
_popstate_listener: Optional[Any] = None
_hotkey_events: dict[str, Callable] = {}
_last_press_time = 0
_hotkey_listener_ready = False
DOUBLE_PRESS_THRESHOLD = 600  # milliseconds


@dataclass
class NavEvent:
    kind: str
    url: str
    data: Any  # FormData-like object
    submitter: Optional[Any] = None


def replaceHTML(tag: Any, html: str) -> None:
    """Replace the HTML content of a tag while preserving scroll position."""
    scroll_top = js.scrollY
    scroll_left = js.scrollX
    r = js.document.createRange()
    r.selectNode(tag)
    fragment = r.createContextualFragment(html)
    tag.replaceWith(fragment)
    js.window.scrollTo(scroll_left, scroll_top)


def debug_log(event_name: str, *args: Any) -> None:
    """Log a debug event to the telemetry system and console."""
    try:
        event_bus = get_main_event_bus()
        event = TelemetryEvent(
            event_type=event_name,
            correlation=TelemetryCorrelation(),
            source="bridge.client"
        )
        event_bus.publish(event)
    except Exception as e:
        print(f"[Drafter Bridge Client] Failed to publish event: {e}")
    
    print(f"[Drafter Bridge Client] {event_name}", *args)


def set_site_title(title: str) -> None:
    """Set the site title in the document and debug panel."""
    global _site_title, _debug_panel
    _site_title = title
    js.document.title = _site_title
    debug_log("site.set_title", _site_title)
    if _debug_panel:
        _debug_panel.setHeaderTitle(_site_title)


def setup_debug_menu(client_bridge: Any) -> None:
    """Set up the debug menu for the application."""
    global _debug_panel
    debug_log("site.setup_debug_menu")
    # This would need the DebugPanel class to be ported as well
    # For now, we'll just log that it was called
    # In a full implementation, you'd import and instantiate DebugPanel here
    print("Debug menu setup called with client bridge:", client_bridge)


def handle_event(event_json: dict) -> None:
    """Handle a telemetry event."""
    global _debug_panel
    try:
        if _debug_panel:
            _debug_panel.handleEvent(event_json)
    except Exception as e:
        print(f"[Drafter Bridge Client] Failed to handle event: {e}")


def make_request(url: str, form_data: Optional[Any] = None, action: str = "submit") -> Request:
    """Create a Request object from the URL and form data."""
    global _request_count
    
    data: dict[str, Any] = {}
    
    if form_data:
        # Extract data from FormData
        # Note: In a real implementation, you'd iterate through the FormData
        # For now, we'll pass it through
        pass
    
    request = Request(
        id=_request_count,
        action=action,
        url=url,
        data=data,
        headers={}
    )
    _request_count += 1
    return request


def add_to_history(request: Request) -> None:
    """Add a request to the browser history."""
    global _site_title
    url = request.url
    request_id = request.id
    
    state = {
        'request_id': request_id,
        'url': url,
    }
    
    # Update document title
    js.document.title = f"{_site_title} - {url}"
    
    # Update URL with route parameter
    # Note: URL manipulation would need additional js support
    debug_log("history.push_state", state, request)


def initiate_request(url: str, data: Optional[Any] = None, remember: bool = True, action: str = "submit") -> None:
    """Initiate a new request."""
    global _navigation_func
    
    if not _navigation_func:
        raise RuntimeError("navigationFunc not set")
    
    debug_log("request.initiated", url, data, _navigation_func)
    
    new_request = make_request(url, data, action)
    
    if remember:
        add_to_history(new_request)
    
    # Call the navigation callback
    _navigation_func(new_request)


def mount_navigation(root: Any, on_navigation: Callable[[NavEvent], None]) -> dict:
    """Mount navigation event handlers."""
    global _click_handler, _submit_handler
    
    # Clean up old handlers if they exist
    if _click_handler:
        root.removeEventListener("click", _click_handler)
    
    # Store the navigation callback
    def handle_click(event: Any) -> None:
        """Handle click events for navigation."""
        target = event.target
        if not target:
            return
        
        # Find nearest element with data-nav or data-call
        nearest_nav_link = target.closest("[data-nav], [data-call]")
        if nearest_nav_link and root.contains(nearest_nav_link):
            event.preventDefault()
            name = nearest_nav_link.getAttribute("data-nav") or nearest_nav_link.getAttribute("data-call")
            if not name:
                return
            
            # Get the form element
            form = js.document.getElementById(DRAFTER_TAG_IDS["FORM"])
            if form:
                # Create FormData from the form
                # Note: This would need proper FormData support
                form_data = None  # Placeholder
                
                nav_event = NavEvent(
                    kind="link",
                    url=name,
                    data=form_data,
                    submitter=nearest_nav_link
                )
                on_navigation(nav_event)
    
    def handle_submit(event: Any) -> None:
        """Handle form submission events."""
        debug_log("dom.form_submit", event)
        event.preventDefault()
        
        submitter = getattr(event, 'submitter', None)
        form_root = js.document.getElementById(DRAFTER_TAG_IDS["FORM"])
        
        if not form_root:
            raise RuntimeError(f"Form element {DRAFTER_TAG_IDS['FORM']} not found")
        
        # Create FormData from the form
        # Note: This would need proper FormData support
        form_data = None  # Placeholder
        
        # Determine the URL
        url = form_root.action if hasattr(form_root, 'action') else None
        if submitter and hasattr(submitter, 'getAttribute'):
            url = submitter.getAttribute("formaction") or url
        
        nav_event = NavEvent(
            kind="form",
            url=url or "",
            data=form_data,
            submitter=submitter
        )
        on_navigation(nav_event)
    
    # Store handlers for cleanup
    _click_handler = handle_click
    _submit_handler = handle_submit
    
    # Attach event listeners
    root.addEventListener("click", handle_click)
    
    form_root = js.document.getElementById(DRAFTER_TAG_IDS["FORM"])
    if form_root:
        if _submit_handler:
            # Clean up old submit handler
            # Note: We can't easily remove it without storing the form element
            pass
        form_root.addEventListener("submit", handle_submit)
    
    debug_log("dom.mount_navigation", "Mounted navigation handlers")
    
    return {"click": True, "submit": True}


def update_site(response: Response, callback: Callable) -> bool:
    """Update the site with a new response."""
    global _navigation_func
    
    _navigation_func = callback
    
    # Get the body element
    element = js.document.getElementById(DRAFTER_TAG_IDS["BODY"])
    if not element:
        raise ValueError(f"Target element {DRAFTER_TAG_IDS['BODY']} not found")
    
    # Update the body content
    body = response.body
    replaceHTML(element, body)
    
    if _debug_panel:
        _debug_panel.setRoute(response.url)
    
    debug_log("dom.updated_body", "update_site called with", response, _navigation_func)
    
    # Mount navigation handlers
    mounted = mount_navigation(element, lambda nav_event: initiate_request(
        nav_event.url,
        nav_event.data,
        True,
        nav_event.kind
    ))
    
    debug_log("dom.mount_navigation", "Mounted navigation handlers:", mounted)
    
    return True


def setup_navigation(handle_visit: Callable) -> None:
    """Set up navigation handlers."""
    global _navigation_func, _popstate_listener
    
    _navigation_func = handle_visit
    
    # Check for initial route in query string
    # Note: This would need proper URL parsing support via js.window.location
    debug_log("site.setup_navigation")
    
    # Set up popstate listener for browser back/forward
    if _popstate_listener:
        js.window.removeEventListener("popstate", _popstate_listener)
    
    def handle_popstate(event: Any) -> None:
        """Handle browser back/forward navigation."""
        global _site_title
        debug_log("history.popstate", event)
        
        state = getattr(event, 'state', None)
        if state and 'request_id' in state:
            request_id = state['request_id']
            url = state['url']
            debug_log("request.back", url, state)
            js.document.title = f"{_site_title} - {url}"
            initiate_request(url, None, False, "back")
        else:
            debug_log("history.popstate_no_state", event)
            js.document.title = _site_title
            initiate_request("index", None, False, "back")
    
    _popstate_listener = handle_popstate
    js.window.addEventListener("popstate", handle_popstate)


def console_log(event: Any) -> None:
    """Log an event to the console."""
    try:
        repr_str = repr(event)
        print("[Drafter]", repr_str)
    except Exception as e:
        print("[Drafter] (unrepresentable event)", e, event)


def register_hotkey(keyCombo: str, callback: Callable[[], None]) -> None:
    """Register a hotkey combination to trigger a callback."""
    global _hotkey_events, _hotkey_listener_ready
    
    combo_lower = keyCombo.lower()
    
    def hotkey_handler(event: Any) -> None:
        """Handle keyboard events for hotkeys."""
        global _last_press_time
        
        key = event.key.lower() if hasattr(event, 'key') else ""
        ctrl = getattr(event, 'ctrlKey', False) or getattr(event, 'metaKey', False)
        
        if ctrl and key in _hotkey_events:
            import time
            now = time.time() * 1000  # Convert to milliseconds
            time_since_last = now - _last_press_time
            
            if time_since_last < DOUBLE_PRESS_THRESHOLD:
                debug_log("hotkey.triggered", key)
                event.preventDefault()
                _hotkey_events[key]()
            
            _last_press_time = now
    
    if not _hotkey_listener_ready:
        js.document.addEventListener("keydown", hotkey_handler)
        _hotkey_listener_ready = True
    
    debug_log("hotkey.register", combo_lower)
    _hotkey_events[combo_lower] = callback
