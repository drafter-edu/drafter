"""
Logging utilities for the bridge module.
"""

from typing import Any


def debug_log(event_name: str, *args: Any) -> None:
    try:
        # Convert args to safe strings to avoid issues with destroyed PyProxies
        safe_args = []
        for arg in args:
            try:
                safe_args.append(str(arg))
            except:
                safe_args.append("<unprintable>")
        print(f"[Drafter Client] {event_name}: ", *safe_args)
    except Exception as e:
        print(f"[Drafter Client] {event_name} (failed to log args: {e})")


def console_log(event) -> None:
    try:
        repr_str = repr(event)
        print(f"[Drafter (Unhandled)] {repr_str}")
    except Exception as e:
        print(
            f"[Drafter/Internal] Failed to log event because of {e}\nOriginal Event:",
            event,
        )
