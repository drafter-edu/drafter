"""
Logging utilities for the bridge module.
"""

import js
from typing import Any


def debug_log(event_name: str, *args: Any) -> None:
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
