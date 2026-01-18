"""
Monitor subsystem for tracking and presenting debug information.

The Monitor lives in the ClientServer and collects telemetry from various
components to provide comprehensive debugging information to developers.
"""

from dataclasses import dataclass, field
from typing import Any, List, Callable
import traceback

from drafter.monitor.bus import get_main_event_bus
from drafter.monitor.telemetry import TelemetryEvent


@dataclass
class Monitor:
    """
    The Monitor tracks all activity in the ClientServer and generates debug information.

    The Monitor is designed to be extremely robust - it should never crash the server.
    All operations are wrapped in try-except blocks to ensure maximum information
    is preserved even if parts of the monitor fail.

    :ivar page_visits: History of all page visits (request/response cycles)
    :ivar current_visit: The currently active page visit being tracked
    :ivar errors: All errors that have been logged
    :ivar warnings: All warnings that have been logged
    :ivar info: All info messages that have been logged
    :ivar enabled: Whether the monitor is currently enabled
    """

    event_history: list[str] = field(default_factory=list)
    routes: list[str] = field(default_factory=list)
    listeners: List[Callable[[TelemetryEvent], None]] = field(default_factory=list)
    enabled: bool = True

    def reset(self) -> None:
        """
        Resets the monitor's internal state.
        """
        self.event_history.clear()
        self.routes.clear()
        self.listeners.clear()

    def listen_for_events(self) -> None:
        """
        Listen for telemetry events on the given event bus.

        :param event_bus: The event bus to listen on
        """
        event_bus = get_main_event_bus()
        event_bus.subscribe("*", self._handle_telemetry_event)

    def register_listener(self, listener: Callable[[Any], None]) -> None:
        """
        Register a listener to receive telemetry events.

        :param listener: A callable that takes a telemetry event
        """
        self.listeners.append(listener)

    def _handle_telemetry_event(self, event: TelemetryEvent) -> None:
        """
        Handle a telemetry event by notifying all registered listeners.

        :param event: The telemetry event to handle
        """
        self.event_history.append(event.event_type)
        for listener in self.listeners:
            try:
                listener(event)
            except Exception as e:
                self._handle_internal_error("listener invocation", e)

    def _handle_internal_error(self, where: str, error: Exception) -> None:
        """
        Handle an internal error in the monitor itself.

        This logs the error but doesn't crash the monitor.

        :param where: Where the error occurred
        :param error: The exception that was raised
        """
        try:
            # Log to stderr for debugging purposes
            # In production, this could be sent to a proper logging system
            import sys

            sys.stderr.write(f"[Monitor Internal Error] in {where}: {error}\n")
            sys.stderr.write(traceback.format_exc())
            sys.stderr.write("\n")
        except Exception:
            # If even logging fails, silently continue
            pass
