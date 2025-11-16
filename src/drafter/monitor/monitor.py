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


class MonitorSnapshot:
    pass


class PageVisitTelemetry:
    pass


@dataclass
class Monitor:
    """
    The Monitor tracks all activity in the ClientServer and generates debug information.

    The Monitor is designed to be extremely robust - it should never crash the server.
    All operations are wrapped in try-except blocks to ensure maximum information
    is preserved even if parts of the monitor fail.

    :ivar page_visits: History of all page visits (request/response/outcome cycles)
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

    # def get_snapshot(
    #     self,
    #     current_state: Any = None,
    #     initial_state: Any = None,
    #     routes: Optional[Dict[str, Callable]] = None,
    #     server_config: Optional[Dict[str, Any]] = None,
    # ) -> MonitorSnapshot:
    #     """
    #     Get a complete snapshot of the monitor's current state.

    #     :param current_state: Current state of the site
    #     :param initial_state: Initial state of the site
    #     :param routes: Available routes
    #     :param server_config: Server configuration
    #     :return: A MonitorSnapshot with all current data
    #     """
    #     try:
    #         return MonitorSnapshot(
    #             timestamp=datetime.now(),
    #             page_visits=list(self.page_visits),
    #             current_state=current_state,
    #             initial_state=initial_state,
    #             routes=routes or {},
    #             errors=list(self.errors),
    #             warnings=list(self.warnings),
    #             info=list(self.info),
    #             server_config=server_config or {},
    #         )
    #     except Exception as e:
    #         self._handle_internal_error("get_snapshot", e)
    #         # Return a minimal snapshot on error
    #         return MonitorSnapshot(
    #             timestamp=datetime.now(),
    #             page_visits=[],
    #             current_state=None,
    #             initial_state=None,
    #             routes={},
    #             errors=self.errors,
    #             warnings=self.warnings,
    #             info=self.info,
    #             server_config={},
    #         )

    #     def generate_debug_html(
    #         self,
    #         current_state: Any = None,
    #         initial_state: Any = None,
    #         routes: Optional[Dict[str, Callable]] = None,
    #         server_config: Optional[Dict[str, Any]] = None,
    #     ) -> str:
    #         """
    #         Generate HTML for the debug panel.

    #         This method is robust and will return a basic error message if generation fails.

    #         :param current_state: Current state of the site
    #         :param initial_state: Initial state of the site
    #         :param routes: Available routes
    #         :param server_config: Server configuration
    #         :return: HTML string for the debug panel
    #         """
    #         if not self.enabled:
    #             return ""

    #         try:
    #             snapshot = self.get_snapshot(
    #                 current_state, initial_state, routes, server_config
    #             )
    #             return self._generate_html_from_snapshot(snapshot)
    #         except Exception as e:
    #             self._handle_internal_error("generate_debug_html", e)
    #             return self._generate_error_fallback_html(e)

    #     def _generate_html_from_snapshot(self, snapshot: MonitorSnapshot) -> str:
    #         """
    #         Generate HTML from a monitor snapshot.

    #         :param snapshot: The snapshot to generate HTML from
    #         :return: HTML string
    #         """
    #         parts = [
    #             "<div class='drafter-debug-panel' id='drafter-debug-panel'>",
    #             "<div class='drafter-debug-header'>",
    #             "<h3>🔍 Debug Monitor</h3>",
    #             "<button onclick='toggleDebugPanel()'>Hide</button>",
    #             "</div>",
    #             "<div class='drafter-debug-content'>",
    #         ]

    #         # Errors section (always visible if present)
    #         if snapshot.errors:
    #             parts.extend(self._render_errors_section(snapshot.errors))

    #         # Warnings section
    #         if snapshot.warnings:
    #             parts.extend(self._render_warnings_section(snapshot.warnings))

    #         # Info section
    #         if snapshot.info:
    #             parts.extend(self._render_info_section(snapshot.info))

    #         # Current state section
    #         parts.extend(self._render_state_section(snapshot.current_state))

    #         # Request/Response/Outcome history
    #         parts.extend(self._render_history_section(snapshot.page_visits))

    #         # Routes section
    #         parts.extend(self._render_routes_section(snapshot.routes))

    #         # Configuration section
    #         parts.extend(self._render_config_section(snapshot.server_config))

    #         parts.extend(
    #             [
    #                 "</div>",  # drafter-debug-content
    #                 "</div>",  # drafter-debug-panel
    #                 self._generate_debug_styles(),
    #                 self._generate_debug_scripts(),
    #             ]
    #         )

    #         return "\n".join(parts)

    #     def _render_errors_section(self, errors: List[DrafterError]) -> List[str]:
    #         """Render the errors section."""
    #         parts = [
    #             "<div class='debug-section debug-errors'>",
    #             f"<h4>❌ Errors ({len(errors)})</h4>",
    #             "<div class='debug-messages'>",
    #         ]

    #         for error in errors[-10:]:  # Show last 10 errors
    #             parts.extend(
    #                 [
    #                     "<div class='debug-message error-message'>",
    #                     f"<div class='message-header'>{html.escape(error.message)}</div>",
    #                     f"<div class='message-where'>at {html.escape(error.where)}</div>",
    #                     f"<div class='message-url'>URL: {html.escape(error.url)}</div>",
    #                     "<details>",
    #                     "<summary>Details</summary>",
    #                     f"<pre>{html.escape(error.details)}</pre>",
    #                     "</details>",
    #                     "</div>",
    #                 ]
    #             )

    #         parts.extend(["</div>", "</div>"])
    #         return parts

    #     def _render_warnings_section(self, warnings: List[DrafterWarning]) -> List[str]:
    #         """Render the warnings section."""
    #         parts = [
    #             "<div class='debug-section debug-warnings'>",
    #             f"<h4>⚠️ Warnings ({len(warnings)})</h4>",
    #             "<div class='debug-messages'>",
    #         ]

    #         for warning in warnings[-10:]:  # Show last 10 warnings
    #             parts.extend(
    #                 [
    #                     "<div class='debug-message warning-message'>",
    #                     f"<div class='message-header'>{html.escape(warning.message)}</div>",
    #                     f"<div class='message-where'>at {html.escape(warning.where)}</div>",
    #                     "</div>",
    #                 ]
    #             )

    #         parts.extend(["</div>", "</div>"])
    #         return parts

    #     def _render_info_section(self, info: List[DrafterInfo]) -> List[str]:
    #         """Render the info section."""
    #         parts = [
    #             "<details class='debug-section debug-info'>",
    #             f"<summary><h4>ℹ️ Info Messages ({len(info)})</h4></summary>",
    #             "<div class='debug-messages'>",
    #         ]

    #         for info_msg in info[-20:]:  # Show last 20 info messages
    #             parts.extend(
    #                 [
    #                     "<div class='debug-message info-message'>",
    #                     f"<div class='message-header'>{html.escape(info_msg.message)}</div>",
    #                     f"<div class='message-where'>at {html.escape(info_msg.where)}</div>",
    #                     "</div>",
    #                 ]
    #             )

    #         parts.extend(["</div>", "</details>"])
    #         return parts

    #     def _render_state_section(self, state: Any) -> List[str]:
    #         """Render the current state section."""
    #         parts = [
    #             "<details class='debug-section debug-state' open>",
    #             "<summary><h4>📊 Current State</h4></summary>",
    #             "<div class='state-content'>",
    #         ]

    #         try:
    #             state_repr = html.escape(repr(state))
    #             parts.append(f"<pre>{state_repr}</pre>")
    #         except Exception as e:
    #             parts.append(
    #                 f"<p class='error'>Failed to render state: {html.escape(str(e))}</p>"
    #             )

    #         parts.extend(["</div>", "</details>"])
    #         return parts

    #     def _render_history_section(self, visits: List[PageVisitTelemetry]) -> List[str]:
    #         """Render the request/response/outcome history section."""
    #         parts = [
    #             "<details class='debug-section debug-history' open>",
    #             f"<summary><h4>📜 Page Visit History ({len(visits)})</h4></summary>",
    #             "<div class='history-content'>",
    #         ]

    #         if not visits:
    #             parts.append("<p>No page visits yet.</p>")
    #         else:
    #             for i, visit in enumerate(reversed(visits[-20:])):  # Show last 20 visits
    #                 parts.extend(self._render_visit(i, visit))

    #         parts.extend(["</div>", "</details>"])
    #         return parts

    #     def _render_visit(self, index: int, visit: PageVisitTelemetry) -> List[str]:
    #         """Render a single page visit."""
    #         parts = [
    #             f"<div class='visit-item'>",
    #             f"<div class='visit-header'>",
    #             f"<span class='visit-number'>#{index + 1}</span>",
    #             f"<span class='visit-url'>{html.escape(visit.request.url)}</span>",
    #         ]

    #         if visit.duration_ms is not None:
    #             parts.append(
    #                 f"<span class='visit-duration'>{visit.duration_ms:.1f}ms</span>"
    #             )

    #         if visit.response:
    #             status_class = (
    #                 "status-ok" if visit.response.status_code < 400 else "status-error"
    #             )
    #             parts.append(
    #                 f"<span class='visit-status {status_class}'>{visit.response.status_code}</span>"
    #             )

    #         parts.extend(
    #             [
    #                 "</div>",
    #                 "<details>",
    #                 "<summary>Details</summary>",
    #                 "<div class='visit-details'>",
    #             ]
    #         )

    #         # Request details
    #         parts.extend(
    #             [
    #                 "<h5>Request</h5>",
    #                 f"<p>Action: {html.escape(visit.request.action)}</p>",
    #                 f"<p>Args: {html.escape(str(visit.request.args))}</p>",
    #                 f"<p>Kwargs: {html.escape(str(visit.request.kwargs))}</p>",
    #             ]
    #         )

    #         # Response details
    #         if visit.response:
    #             payload_type = type(visit.response.payload).__name__
    #             body_length = len(visit.response.body) if visit.response.body else 0
    #             has_errors = len(visit.response.errors) > 0
    #             has_warnings = len(visit.response.warnings) > 0
    #             parts.extend(
    #                 [
    #                     "<h5>Response</h5>",
    #                     f"<p>Payload Type: {html.escape(payload_type)}</p>",
    #                     f"<p>Body Length: {body_length} chars</p>",
    #                     f"<p>Errors: {has_errors}</p>",
    #                     f"<p>Warnings: {has_warnings}</p>",
    #                 ]
    #             )

    #         # Outcome details
    #         if visit.outcome:
    #             parts.extend(
    #                 [
    #                     "<h5>Outcome</h5>",
    #                     f"<p>Status: {html.escape(visit.outcome.message)}</p>",
    #                 ]
    #             )

    #         parts.extend(
    #             [
    #                 "</div>",
    #                 "</details>",
    #                 "</div>",
    #             ]
    #         )

    #         return parts

    #     def _render_routes_section(self, routes: Dict[str, Any]) -> List[str]:
    #         """Render the routes section."""
    #         parts = [
    #             "<details class='debug-section debug-routes'>",
    #             f"<summary><h4>🗺️ Available Routes ({len(routes)})</h4></summary>",
    #             "<ul class='routes-list'>",
    #         ]

    #         for url, func in sorted(routes.items()):
    #             func_name = getattr(func, "__name__", str(func))
    #             parts.append(
    #                 f"<li><code>{html.escape(url)}</code> → {html.escape(func_name)}</li>"
    #             )

    #         parts.extend(["</ul>", "</details>"])
    #         return parts

    #     def _render_config_section(self, config: Dict[str, Any]) -> List[str]:
    #         """Render the configuration section."""
    #         parts = [
    #             "<details class='debug-section debug-config'>",
    #             "<summary><h4>⚙️ Configuration</h4></summary>",
    #             "<pre>",
    #         ]

    #         try:
    #             config_str = json.dumps(config, indent=2, default=str)
    #             parts.append(html.escape(config_str))
    #         except Exception as e:
    #             parts.append(f"Failed to serialize config: {html.escape(str(e))}")

    #         parts.extend(["</pre>", "</details>"])
    #         return parts

    #     def _generate_debug_styles(self) -> str:
    #         """Generate CSS styles for the debug panel."""
    #         return """
    # <style>
    # .drafter-debug-panel {
    #     position: fixed;
    #     bottom: 0;
    #     left: 0;
    #     right: 0;
    #     max-height: 50vh;
    #     background: #1e1e1e;
    #     color: #d4d4d4;
    #     font-family: 'Consolas', 'Monaco', monospace;
    #     font-size: 12px;
    #     border-top: 3px solid #007acc;
    #     overflow-y: auto;
    #     z-index: 10000;
    #     box-shadow: 0 -2px 10px rgba(0,0,0,0.3);
    # }

    # .drafter-debug-header {
    #     display: flex;
    #     justify-content: space-between;
    #     align-items: center;
    #     padding: 10px 15px;
    #     background: #252526;
    #     border-bottom: 1px solid #007acc;
    #     position: sticky;
    #     top: 0;
    #     z-index: 100;
    # }

    # .drafter-debug-header h3 {
    #     margin: 0;
    #     color: #007acc;
    #     font-size: 16px;
    # }

    # .drafter-debug-header button {
    #     background: #007acc;
    #     color: white;
    #     border: none;
    #     padding: 5px 15px;
    #     cursor: pointer;
    #     border-radius: 3px;
    #     font-size: 12px;
    # }

    # .drafter-debug-header button:hover {
    #     background: #005a9e;
    # }

    # .drafter-debug-content {
    #     padding: 15px;
    # }

    # .debug-section {
    #     margin-bottom: 20px;
    #     padding: 10px;
    #     background: #252526;
    #     border-radius: 5px;
    #     border-left: 4px solid #007acc;
    # }

    # .debug-section h4 {
    #     margin: 0 0 10px 0;
    #     color: #4ec9b0;
    #     font-size: 14px;
    # }

    # .debug-errors {
    #     border-left-color: #f48771;
    # }

    # .debug-warnings {
    #     border-left-color: #cca700;
    # }

    # .debug-message {
    #     padding: 8px;
    #     margin: 5px 0;
    #     background: #1e1e1e;
    #     border-radius: 3px;
    # }

    # .error-message {
    #     border-left: 3px solid #f48771;
    # }

    # .warning-message {
    #     border-left: 3px solid #cca700;
    # }

    # .info-message {
    #     border-left: 3px solid #007acc;
    # }

    # .message-header {
    #     font-weight: bold;
    #     color: #dcdcaa;
    #     margin-bottom: 5px;
    # }

    # .message-where {
    #     color: #9cdcfe;
    #     font-size: 11px;
    # }

    # .message-url {
    #     color: #ce9178;
    #     font-size: 11px;
    # }

    # .visit-item {
    #     margin: 10px 0;
    #     padding: 10px;
    #     background: #1e1e1e;
    #     border-radius: 3px;
    # }

    # .visit-header {
    #     display: flex;
    #     gap: 10px;
    #     align-items: center;
    #     margin-bottom: 5px;
    # }

    # .visit-number {
    #     color: #569cd6;
    #     font-weight: bold;
    # }

    # .visit-url {
    #     color: #ce9178;
    #     flex-grow: 1;
    # }

    # .visit-duration {
    #     color: #b5cea8;
    #     font-size: 11px;
    # }

    # .visit-status {
    #     padding: 2px 6px;
    #     border-radius: 3px;
    #     font-size: 11px;
    #     font-weight: bold;
    # }

    # .status-ok {
    #     background: #4ec9b0;
    #     color: #1e1e1e;
    # }

    # .status-error {
    #     background: #f48771;
    #     color: #1e1e1e;
    # }

    # .routes-list {
    #     list-style: none;
    #     padding: 0;
    #     margin: 0;
    # }

    # .routes-list li {
    #     padding: 5px 0;
    #     color: #9cdcfe;
    # }

    # pre {
    #     background: #1e1e1e;
    #     padding: 10px;
    #     border-radius: 3px;
    #     overflow-x: auto;
    #     color: #d4d4d4;
    # }

    # details summary {
    #     cursor: pointer;
    #     user-select: none;
    # }

    # details summary:hover {
    #     color: #007acc;
    # }
    # </style>
    # """

    #     def _generate_debug_scripts(self) -> str:
    #         """Generate JavaScript for the debug panel."""
    #         return """
    # <script>
    # function toggleDebugPanel() {
    #     const panel = document.getElementById('drafter-debug-panel');
    #     if (panel) {
    #         panel.style.display = panel.style.display === 'none' ? 'block' : 'none';
    #     }
    # }

    # // Make debug panel draggable (optional enhancement)
    # (function() {
    #     const panel = document.getElementById('drafter-debug-panel');
    #     if (!panel) return;

    #     // Add keyboard shortcut to toggle panel (Ctrl+Shift+D)
    #     document.addEventListener('keydown', function(e) {
    #         if (e.ctrlKey && e.shiftKey && e.key === 'D') {
    #             e.preventDefault();
    #             toggleDebugPanel();
    #         }
    #     });
    # })();
    # </script>
    # """

    #     def _generate_error_fallback_html(self, error: Exception) -> str:
    #         """
    #         Generate a minimal error fallback HTML when debug generation fails.

    #         :param error: The exception that caused the failure
    #         :return: Minimal error HTML
    #         """
    #         error_msg = html.escape(str(error))
    #         error_trace = html.escape(traceback.format_exc())

    #         return f"""
    # <div class='drafter-debug-panel' style='position: fixed; bottom: 0; left: 0; right: 0; background: #1e1e1e; color: #d4d4d4; padding: 15px; border-top: 3px solid #f48771; z-index: 10000;'>
    #     <h3 style='color: #f48771; margin: 0 0 10px 0;'>⚠️ Debug Monitor Error</h3>
    #     <p>The debug monitor encountered an error while generating debug information:</p>
    #     <pre style='background: #252526; padding: 10px; border-radius: 3px; overflow-x: auto;'>{error_msg}</pre>
    #     <details>
    #         <summary>Stack Trace</summary>
    #         <pre style='background: #252526; padding: 10px; border-radius: 3px; overflow-x: auto;'>{error_trace}</pre>
    #     </details>
    # </div>
    # """

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
