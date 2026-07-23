"""
Logging utilities for the bridge module.
"""

from typing import Any

import js


def debug_log(event_name: str, *args: Any) -> None:
    """Log a named bridge debug event to the browser console.

    Arguments are converted to real JS objects (via pyodide's to_js) so the
    console shows inspectable values rather than proxies. If console logging
    fails (e.g. destroyed PyProxies or unconvertible values), falls back to
    print with stringified arguments, and finally to printing just the event
    name. Never raises.

    Args:
        event_name: Dotted identifier for the event (e.g.
            "client.add_to_history").
        *args: Arbitrary values to log alongside the event name.
    """
    # First try logging using console.log
    try:
        # Explicitly try to convert each argument to an actual JS object instead of a proxy
        converted = []
        for arg in args:
            from pyodide.ffi import to_js

            converted.append(to_js(arg))
        js.console.log(f"[Drafter Client] {event_name}: ", *converted)
    except Exception as e:
        js.console.error(f"[Drafter Client] Failed to log event {event_name}: {e}")
        try:
            # Convert args to safe strings to avoid issues with destroyed PyProxies
            safe_args = []
            for arg in args:
                try:
                    safe_args.append(str(arg))
                except Exception:
                    safe_args.append("<unprintable>")
            print(f"[Drafter Client*] {event_name}: ", *safe_args)
        except Exception as e:
            print(f"[Drafter Client!] {event_name} (failed to log args: {e})")


def console_log(event) -> None:
    """Log an unhandled event to the browser console.

    Used as the last resort for server events that nothing else handled.
    Falls back to printing the event's repr if console logging fails, and to
    a diagnostic print if even that fails. Never raises.

    Args:
        event: The unhandled event to log.
    """
    try:
        js.console.log("[Drafter (Unhandled)]", event)
    except Exception:
        try:
            repr_str = repr(event)
            print(f"[Drafter (Unhandled)] {repr_str}")
        except Exception as e:
            print(
                f"[Drafter/Internal] Failed to log event because of {e}\nOriginal Event:",
                event,
            )
