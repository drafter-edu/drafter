"""
The ClientServer: Drafter's in-browser request/response engine.

Defines the `ClientServer` class, which owns the site, router, state, and
event bus for one running application instance. It handles configuration
and startup, dispatches visits through the router to route functions,
verifies and commits the resulting payloads, and reports errors through
the telemetry system.
"""

import time
from dataclasses import dataclass
from typing import Any, Literal

from drafter.client_server.context import Scope
from drafter.components.utilities.contracts import HelperContext
from drafter.components.utilities.registry import COMPONENT_CONTRACT_REGISTRY
from drafter.config.client_server import ClientServerConfiguration
from drafter.configuration import get_system_configuration
from drafter.data.channel import Message
from drafter.data.correlation import Correlation
from drafter.data.details.config import (
    InitialConfigurationEvent,
    ResetServerEvent,
    ServerInitializedEvent,
    UpdatedConfigurationEvent,
)
from drafter.data.details.request import (
    RequestEvent,
    RequestParseEvent,
    ResponseEvent,
)
from drafter.data.details.routes import RouteAddedEvent
from drafter.data.details.state import UpdatedStateEvent
from drafter.data.error_explainer import explain
from drafter.data.errors import (
    CATEGORY_PAYLOAD,
    CATEGORY_REQUEST,
    CATEGORY_SYSTEM,
    SEVERITY_INFO,
    STATUS_BAD_REQUEST,
    STATUS_ERROR,
    STATUS_NOT_FOUND,
    ErrorDetails,
    envelope_from_exception,
)
from drafter.data.request import Request
from drafter.data.response import Response
from drafter.data.telemetry import ErrorRecord, TelemetryMetadata
from drafter.history.state import SiteState
from drafter.monitor.audit import log_error, log_record
from drafter.monitor.bus import EventBus, Subscription
from drafter.payloads.kinds.error_page import SimpleErrorPage
from drafter.payloads.payloads import ResponsePayload
from drafter.payloads.target import Target
from drafter.payloads.verification import (
    verify_page_state_history,
    verify_response_payload_type,
)
from drafter.router.routes import Router
from drafter.site.initial_site_data import InitialSiteData
from drafter.site.site import DRAFTER_TAG_CLASSES, Site

ServerPhases = Literal[
    "initializing",
    "initialized",
    "configuring",
    "rendering",
    "starting",
    "started",
    "visiting",
    "committing",
    "idle",
]
"""The lifecycle phases a ClientServer moves through, from construction
("initializing") through startup ("starting", "configuring", "rendering",
"started") to request handling ("visiting", "committing", "idle"). See the
ClientServer docstring for what each phase means."""


@dataclass
class ClientServer:
    """
    The ClientServer is responsible for handling requests from the BridgeClient,
    routing them to the appropriate functions, and returning responses.

    The Server can be in one of the following phases:

    - initializing: During the initial ClientServer constructor call
    - initialized: After the constructor has completed, but before the `do_start` method is called
    - starting: During the execution of the `do_start` method
    - configuring: During the processing of static and dynamic configuration
    - rendering: During the rendering of the initial site into its HTML meta-structure (NOT the student's page content)
    - started: After the `do_start` method has completed, but before the first request is processed
    - visiting: After the first request is processed, and the server is fully operational
    - committing: During the process of committing changes or updates from the response.
    - idle: When the server is not processing a request, but is still running and can receive requests. This is the default state of the server after it has started and is waiting for requests.

    Attributes:
        custom_name: A custom name for the server, useful for debugging.
        instance_root: Virtual-filesystem folder this instance's relative
            paths resolve to when several instances share one interpreter,
            or None for the interpreter-wide default.
        event_bus: The EventBus used to publish and subscribe to telemetry events.
        site: The Site instance describing the outer site structure and configuration.
        router: The Router instance that handles URL routing.
        state: The state information about the student's site.
        response_count: A counter for the number of responses made, used to assign unique IDs.
        requests: A Scope stack tracking the requests currently being processed.
        start_time: Timestamp recorded by `start_timer` for measuring request duration.
        phase: The current lifecycle phase of the server (see above).
        started: Whether `do_start` has completed.
    """

    custom_name: str
    state: SiteState
    phase: ServerPhases = "initializing"
    started: bool = False

    def __init__(self, custom_name: str) -> None:
        self.custom_name = custom_name
        # Virtual-filesystem folder this instance's relative paths resolve to
        # (e.g. "/instances/demo-1") when several instances share one
        # interpreter. None means the interpreter-wide default. Assigned by
        # run_client_bridge from the configure_instance handoff.
        self.instance_root: str | None = None
        self.event_bus = EventBus()

        server_initialized_event = ServerInitializedEvent(
            metadata=TelemetryMetadata(source="client_server.server_initialized"),
            correlation=Correlation(phase=self.phase),
        )
        self.event_bus.publish(server_initialized_event)
        self.site = Site()
        self.router = Router()
        self.state = SiteState()
        self.response_count = 0

        self.requests = Scope()
        self.start_time = 0.0
        # Best-known generated route call per in-flight request id, as a
        # (call_string, is_exact) pair: an approximation from the raw request
        # is stored when the route is resolved, upgraded to the exact bound
        # call once argument preparation succeeds, and attached to any error
        # envelope raised during the visit (see make_visit_error).
        self._route_call_reprs: dict[int, tuple[str, bool]] = {}
        self.transition("initialized")

    def reset(self) -> None:
        """Reset the server to its initial state.

        Clears state, router, site, and counters.
        """
        self.state.reset()
        self.router.reset()
        # TODO: Should this also copy the default -> current configurations?
        self.site.reset()
        # self.monitor.reset()
        self.response_count = 0
        self.requests.reset()
        log_record(
            ResetServerEvent(),
            "client_server.reset",
        )

    def transition(self, new_phase: ServerPhases):
        """Transition the server to a new phase.

        Args:
            new_phase: The new phase to transition to.
        """
        self.phase = new_phase

    def process_dynamic_configuration(self):
        """Initialize the runtime configuration from a copy of the defaults.

        Separates default and current configurations so runtime changes
        don't affect defaults. Call only during server startup.

        Returns:
            ClientServerConfiguration: The applied configuration.
        """
        # Snapshot the shared defaults: each server must own its active
        # configuration so runtime changes on one instance (reconfigure,
        # configure_instance for a later instance) never leak into another
        # server sharing the interpreter.
        configuration = self.get_default_configuration().copy()
        self.site.set_configuration(configuration)
        return configuration

    def is_configured(self) -> bool:
        """Check if the server has been configured with a configuration instance."""
        return self.site._configuration is not None

    def reconfigure(self, update_default: bool = False, **kwargs):
        """Update active server configuration and optionally the defaults.

        Args:
            update_default: Whether to also update default configuration.
            **kwargs: Configuration keys and values to update.
        """
        for key, value in kwargs.items():
            if self.is_configured():
                self.site.update_configuration(key, value)
                if update_default:
                    self.get_default_configuration().update_configuration(key, value)
            else:
                self.get_default_configuration().update_configuration(key, value)
            log_record(
                UpdatedConfigurationEvent(
                    key=key, value=value, update_default=update_default
                ),
                "client_server.reconfigure",
                request_id=self.get_current_request_id(),
            )

    def get_config_setting(self, key: str):
        """Retrieve a configuration setting value.

        Args:
            key: Configuration key to retrieve.

        Returns:
            The configuration value associated with the key.

        TODO:
            Check for non-existent keys and raise an error.
        """
        # TODO: Check for non-existent keys and raise an error
        if self.started:
            return getattr(self.site._configuration, key)
        else:
            return getattr(self.get_default_configuration(), key)

    def reconfigure_flip(self, key: str):
        """Toggle a boolean configuration setting.

        Args:
            key: Boolean configuration key to flip.
        """
        current_value = self.get_config_setting(key)
        self.reconfigure(**{key: not current_value})

    def do_start(self, initial_state: Any = None) -> None:
        """Start the server and register default routes.

        Args:
            initial_state: Optional initial state for the server.
        """
        self.transition("starting")
        if initial_state is not None:
            try:
                self.state.update(initial_state)
                log_error(
                    ErrorDetails(
                        id="state.initialized",
                        category=CATEGORY_SYSTEM,
                        message="Initializing server state",
                        severity=SEVERITY_INFO,
                        details=f"Initial state: {repr(initial_state)}",
                    ),
                    "client_server.start",
                )
            except Exception as e:
                log_error(
                    envelope_from_exception(
                        e,
                        "state.initialization_failed",
                        CATEGORY_SYSTEM,
                        message="Failed to initialize server state",
                        details=f"Initial state: {repr(initial_state)}",
                    ),
                    "client_server.start",
                )
        # Register any default routes, if needed
        self.register_system_routes()
        # All done!
        self.transition("started")
        self.started = True
        log_error(
            ErrorDetails(
                id="server.started",
                category=CATEGORY_SYSTEM,
                message="Started ClientServer",
                severity=SEVERITY_INFO,
                details=f"Server name: {self.custom_name}",
            ),
            "client_server.start",
        )

    def register_system_routes(self):
        """Register system routes like --error, --about, --reset.

        For each system route, uses the handler override from the current
        configuration's `system_routes` if present, otherwise the default
        handler. Routes already registered in the router are left alone.
        """
        from drafter.router.system_routes import _SYSTEM_ROUTES

        configuration = self.get_current_configuration()
        for route, default_handler in _SYSTEM_ROUTES.items():
            route_handler = configuration.system_routes.get(route) or default_handler
            if not self.router.has_route(route):
                self.add_route(route, route_handler, True)

    def make_visit_error(
        self,
        error_id: str,
        category: str,
        message: str,
        request: Request,
        *,
        details: str = "",
        data: dict[str, Any] | None = None,
        status_code: str | None = None,
        exception: Exception | None = None,
        source: str = "client_server.visit",
    ) -> ErrorDetails:
        """Build a canonical envelope for a visit failure and emit telemetry.

        This is the single path for visit lifecycle failures: the canonical
        `ErrorDetails` is created first, telemetry is emitted from it,
        and the returned envelope is raised directly.

        Every envelope automatically carries the structured request
        description (`data["request"]`) and, when known, the generated route
        call that led to the failure (`data["route_call"]` plus
        `data["route_call_exact"]`) — the exact bound call string once
        argument preparation succeeded, or a best-effort approximation from
        the raw request values before that.

        Args:
            error_id: Stable, code-like id (e.g. `request.route_not_found`).
            category: Canonical error category.
            message: Human-safe message.
            request: The request being processed (for correlation context).
            details: Developer-focused free-text details.
            data: Extra structured details for this failure (e.g. the
                payload); merged with the automatic request/route-call keys.
            status_code: Symbolic status string; defaults to
                `STATUS_ERROR`.
            exception: Originating exception, if any (for traceback capture).
            source: The component/function reporting the failure.

        Returns:
            ErrorDetails ready to be raised by the caller.
        """
        context = Correlation(route=request.url, request_id=request.id, phase="visit")
        resolved_status = status_code if status_code is not None else STATUS_ERROR
        merged_data: dict[str, Any] = dict(data or {})
        call_repr = self._route_call_reprs.get(request.id)
        if call_repr is not None and "route_call" not in merged_data:
            merged_data["route_call"], merged_data["route_call_exact"] = call_repr
        merged_data.setdefault("request", request)
        if exception is not None:
            envelope = envelope_from_exception(
                exception,
                error_id,
                category,
                message=message,
                details=details,
                data=merged_data,
                context=context,
                status_code=resolved_status,
            )
        else:
            explanation = explain(None, error_id, category)
            envelope = ErrorDetails(
                id=error_id,
                category=category,
                message=message,
                details=details,
                data=merged_data,
                friendly_title=explanation.title,
                friendly_message=explanation.message,
                friendly_steps=explanation.steps,
                context=context,
                status_code=resolved_status,
            )
        log_error(envelope, source)
        return envelope

    def get_route(self, request: Request):
        """Resolve a request URL to a route handler function.

        Args:
            request: Request with URL to resolve.

        Returns:
            Callable: The route handler function.

        Raises:
            ErrorDetails: If no route matches the URL (404).
        """
        route_func = self.router.get_route(request.url)
        if route_func is None:
            raise self.make_visit_error(
                "request.route_not_found",
                CATEGORY_REQUEST,
                f"No route found for URL: {request.url}",
                request,
                status_code=STATUS_NOT_FOUND,
            )
        return route_func

    def _get_extra_dependencies(
        self, request: Request, configuration: ClientServerConfiguration
    ) -> dict[str, Any]:
        """Get extra dependencies to inject into route handlers.

        Alongside the fixed framework values, the component that emitted the
        event may contribute helpers declared in its contract (e.g. Map's
        ``add_marker``); those are materialized here from the live element
        that triggered the request. Framework values are added last so a
        component helper can never shadow them.

        Returns:
            dict: Mapping of dependency names to instances.
        """
        dependencies: dict[str, Any] = {}
        element = request.button_pressed
        tag = getattr(element, "tagName", None) if element is not None else None
        if isinstance(tag, str) and tag:
            helpers = COMPONENT_CONTRACT_REGISTRY.helpers_for(tag, request.action)
            if helpers:
                context = HelperContext(element=element, values=dict(request.kwargs))
                for helper in helpers:
                    dependencies[helper.name] = helper.factory(context)
        dependencies.update(
            {
                "_server": self,
                "_configuration": configuration,
                "_request": request,
            }
        )
        return dependencies

    @staticmethod
    def _approximate_route_call(route_func, request: Request) -> str:
        """Best-effort route call string from the raw request values.

        Used before argument preparation has produced the exact bound call:
        the raw form/component values stand in for the real arguments, so
        the result shows "as much as has been constructed" so far. Framework
        bookkeeping entries (keys with the ``--`` prefix, like the submit
        button) are not part of the student's call and are left out.
        """
        name = getattr(route_func, "__name__", "") or request.url or "route"
        try:
            arguments = ", ".join(
                f"{key}={value!r}"
                for key, value in request.kwargs.items()
                if not str(key).startswith("--")
            )
        except Exception:
            arguments = "..."
        return f"{name}({arguments})"

    def execute_route(
        self,
        route_func,
        request: Request,
        configuration: ClientServerConfiguration,
    ) -> tuple[Any, str]:
        """Prepare arguments and invoke a route handler.

        Args:
            route_func: Handler function to invoke.
            request: Request providing arguments.
            configuration: Current server configuration.

        Returns:
            Tuple of (payload result, string representation of arguments).

        Raises:
            ErrorDetails: On argument parsing or execution failures.
        """
        # Call the route function to get the payload
        try:
            args, kwargs, representation, provenance = self.router.prepare_arguments(
                request,
                self.state.current,
                configuration,
                self._get_extra_dependencies(request, configuration),
            )
            # The exact bound call is now known; error envelopes raised for
            # the rest of this visit will carry it (see make_visit_error).
            self._route_call_reprs[request.id] = (representation, True)
            log_record(
                RequestParseEvent(
                    request_id=request.id,
                    representation=representation,
                    arguments=list(provenance),
                ),
                "client_server.execute_route",
                route=request.url,
                request_id=request.id,
            )
        except Exception as e:
            raise self.make_visit_error(
                "request.argument_parsing_failed",
                CATEGORY_REQUEST,
                f"Error while parsing arguments for request to URL {request.url}: {e}",
                request,
                status_code=STATUS_BAD_REQUEST,
                exception=e,
            ) from e
        try:
            return route_func(*args, **kwargs), representation
        except Exception as e:
            raise self.make_visit_error(
                "request.route_execution_failed",
                CATEGORY_REQUEST,
                f"Error while processing request for URL '{request.url}': {e}",
                request,
                status_code=STATUS_ERROR,
                exception=e,
            ) from e

    def verify_payload(
        self, request: Request, payload: Any, configuration: ClientServerConfiguration
    ):
        """Validate payload type and payload-specific rules.

        Args:
            request: Associated request for error context.
            payload: Payload to verify.
            configuration: Current server configuration.

        Raises:
            ErrorDetails: If payload verification fails.
        """
        # Check that it's a valid payload type
        possible_incorrect_type = verify_response_payload_type(request, payload)
        if possible_incorrect_type is not None:
            raise self.make_visit_error(
                "payload.verification_failed",
                CATEGORY_PAYLOAD,
                f"Payload verification failed for URL {request.url}: {possible_incorrect_type}",
                request,
                data={"payload": payload},
                status_code=STATUS_ERROR,
            )
        # Payload specific verification
        try:
            possible_failure = payload.verify(
                self.router, self.state, configuration, request
            )
        except Exception as e:
            raise self.make_visit_error(
                "payload.verification_failed",
                CATEGORY_PAYLOAD,
                f"Payload verification failed for URL {request.url}: {e}",
                request,
                data={"payload": payload},
                status_code=STATUS_ERROR,
                exception=e,
            ) from e
        if possible_failure is not None:
            raise self.make_visit_error(
                "payload.verification_failed",
                CATEGORY_PAYLOAD,
                f"Payload verification failed for URL {request.url}: {possible_failure.message}",
                request,
                data={"payload": payload},
                status_code=STATUS_ERROR,
            )

    def render_payload(
        self,
        request: Request,
        payload: ResponsePayload,
        configuration: ClientServerConfiguration,
    ) -> str | None:
        """Render a payload to HTML string.

        Args:
            request: Associated request for error context.
            payload: Payload to render.
            configuration: Current server configuration.

        Returns:
            str or None: HTML output of the rendered payload.

        Raises:
            ErrorDetails: If rendering fails.
        """
        # Render the payload
        try:
            return payload.render(self.state, configuration)
        except Exception as e:
            raise self.make_visit_error(
                "payload.rendering_failed",
                CATEGORY_PAYLOAD,
                f"Payload rendering failed for URL {request.url}: {e}",
                request,
                data={"payload": payload},
                status_code=STATUS_ERROR,
                exception=e,
            ) from e

    def format_payload(
        self,
        request: Request,
        representation: str,
        payload: ResponsePayload,
        configuration: ClientServerConfiguration,
    ) -> str:
        """Format a payload for history panel display.

        Args:
            request: Associated request for error context.
            representation: String representation of arguments.
            payload: Payload to format.
            configuration: Current server configuration.

        Returns:
            str: Formatted payload representation.

        Raises:
            ErrorDetails: If formatting fails.
        """
        # Format the payload for display in the history panel
        try:
            return payload.format(self.state, representation, configuration)
        except Exception as e:
            raise self.make_visit_error(
                "payload.formatting_failed",
                CATEGORY_PAYLOAD,
                f"Payload formatting failed for URL {request.url}: {e}",
                request,
                data={"payload": payload},
                status_code=STATUS_ERROR,
                exception=e,
            ) from e

    def handle_state_updates(
        self,
        request: Request,
        payload: ResponsePayload,
        configuration: ClientServerConfiguration,
    ) -> None:
        """Extract and apply state updates from a payload.

        Args:
            request: Associated request for error context.
            payload: Payload containing state updates.
            configuration: Current server configuration.

        Raises:
            ErrorDetails: If state verification or update fails.
        """
        is_updated, updated_state = payload.get_state_updates()
        if is_updated:
            # Check that the state update will be valid
            possible_state_update_issue = verify_page_state_history(
                request, updated_state, self.state.history
            )
            if possible_state_update_issue is not None:
                raise self.make_visit_error(
                    "payload.state_verification_failed",
                    CATEGORY_PAYLOAD,
                    f"State verification failed for URL {request.url}: {possible_state_update_issue}",
                    request,
                    data={"payload": payload},
                    status_code=STATUS_ERROR,
                    source="client_server.handle_state_updates",
                )
            try:
                self.state.update(updated_state)
                log_record(
                    UpdatedStateEvent.from_state(updated_state),
                    "client_server.handle_state_updates",
                    request_id=request.id,
                    route=request.url,
                )
            except Exception as e:
                raise self.make_visit_error(
                    "payload.state_update_failed",
                    CATEGORY_PAYLOAD,
                    f"Failed to update server state from payload for URL {request.url}: {e}",
                    request,
                    data={"updated_state": updated_state},
                    status_code=STATUS_ERROR,
                    exception=e,
                    source="client_server.handle_state_updates",
                ) from e

    def start_timer(self):
        """Record the current time as the start of a request."""
        self.start_time = time.time()

    def check_timer(self) -> float:
        """Calculate elapsed time since start_timer() in milliseconds.

        Returns:
            float: Elapsed time in milliseconds.
        """
        return (time.time() - self.start_time) * 1000  # in milliseconds

    def do_visit(self, request: Request) -> Any:
        """Process a request and return the appropriate response.

        Orchestrates route resolution, execution, verification, rendering,
        and state updates before returning a Response to the client.

        Request-scoped warnings (warning-level telemetry correlated with this
        request's id) emitted during the visit are collected and attached to
        the outgoing response (success or error), so they appear in both
        telemetry and response metadata.

        Args:
            request: The request to process.

        Returns:
            Response: Success or error response to send to the client.
        """
        from drafter.client_server.commands import get_main_event_bus

        self.start_timer()
        self.transition("visiting")
        log_record(
            RequestEvent.from_request(request),
            "client_server.visit",
            route=request.url,
            request_id=request.id,
        )
        visit_warnings: list[ErrorDetails] = []

        def capture_warning(event):
            if isinstance(event, ErrorRecord) and event.error is not None:
                visit_warnings.append(event.error)

        warning_subscription = get_main_event_bus().subscribe(
            "*",
            capture_warning,
            filter=lambda event: (
                event.metadata.level == "warning"
                and event.correlation.request_id == request.id
                and isinstance(event, ErrorRecord)
            ),
        )
        try:
            with self.requests.push(request):
                try:
                    # TODO: Most of these should be private methods
                    configuration = self.get_current_configuration()
                    route_func = self.get_route(request)
                    # Until the exact bound call is known, remember a
                    # best-effort approximation for error envelopes.
                    self._route_call_reprs[request.id] = (
                        self._approximate_route_call(route_func, request),
                        False,
                    )
                    payload, representation = self.execute_route(
                        route_func, request, configuration
                    )
                    self.verify_payload(request, payload, configuration)
                    body = self.render_payload(request, payload, configuration)
                    formatted_body = self.format_payload(
                        request, representation, payload, configuration
                    )
                    self.handle_state_updates(request, payload, configuration)
                    messages = self.get_messages(request, payload, configuration)
                    target = self.get_target(request, payload, configuration)
                except ErrorDetails as ve:
                    return self.make_error_response(
                        request,
                        ve,
                        warnings=visit_warnings,
                    )

                # Return successfully
                try:
                    response = self.make_success_response(
                        request.id,
                        request.url,
                        body,
                        payload,
                        messages,
                        target,
                        warnings=visit_warnings,
                    )
                except Exception as e:
                    envelope = self.make_visit_error(
                        "system.response_creation_failed",
                        CATEGORY_SYSTEM,
                        f"Failed to create success response for URL {request.url}: {e}",
                        request,
                        status_code=STATUS_ERROR,
                        exception=e,
                    )
                    return self.make_error_response(
                        request,
                        envelope,
                        warnings=visit_warnings,
                    )
                log_record(
                    ResponseEvent.from_response(
                        response, formatted_body, self.check_timer()
                    ),
                    "client_server.visit",
                    route=request.url,
                    request_id=request.id,
                    response_id=response.id,
                )
                self.transition("committing")
                return response
        finally:
            self._route_call_reprs.pop(request.id, None)
            get_main_event_bus().unsubscribe(warning_subscription)

    def make_success_response(
        self,
        request_id: int,
        url: str,
        body: str | None,
        payload: ResponsePayload,
        messages: list[Message],
        target: Target | None,
        warnings: list[ErrorDetails] | None = None,
    ) -> Response:
        """Construct a successful response from request processing results.

        Args:
            request_id: ID of the associated request.
            url: URL that was processed.
            body: Rendered HTML body content.
            payload: ResponsePayload that generated the body.
            messages: Channel messages to execute on the client.
            target: Optional target selector for fragment updates.
            warnings: Request-scoped warnings (non-fatal issues) generated
                while processing the request, attached to the response.

        Returns:
            Response: Success response ready to send to the client.
        """
        response = Response(
            id=self.response_count,
            request_id=request_id,
            payload=payload,
            body=body,
            url=url,
            target=target,
            warnings=list(warnings) if warnings else [],
        )
        response.send_messages(messages)
        self.response_count += 1

        return response

    def get_target(
        self,
        request: Request,
        payload: ResponsePayload,
        configuration: ClientServerConfiguration,
    ) -> "Target | None":
        """Extract the Target object from a payload.

        Args:
            request: Associated request for error context.
            payload: Payload to extract target from.
            configuration: Current server configuration.

        Returns:
            Optional[Target]: Target object (e.g., for Fragment updates).

        Raises:
            ErrorDetails: If target retrieval fails.
        """
        try:
            return payload.get_target(request)
        except Exception as e:
            raise self.make_visit_error(
                "payload.target_retrieval_failed",
                CATEGORY_PAYLOAD,
                f"Payload target retrieval failed for URL {request.url}: {e}",
                request,
                data={"payload": payload},
                status_code=STATUS_ERROR,
                exception=e,
            ) from e
        return None

    def get_messages(
        self,
        request: Request,
        payload: ResponsePayload,
        configuration: ClientServerConfiguration,
    ) -> list[Message]:
        """Extract channel messages from a payload.

        Args:
            request: Associated request for error context.
            payload: Payload to extract messages from.
            configuration: Current server configuration.

        Returns:
            list[Message]: Messages to execute on the client.

        Raises:
            ErrorDetails: If message retrieval fails.
        """
        try:
            messages = payload.get_messages(self.state, configuration)
            if messages is None:
                messages = []
        except Exception as e:
            raise self.make_visit_error(
                "payload.message_retrieval_failed",
                CATEGORY_PAYLOAD,
                f"Payload message retrieval failed for URL {request.url}: {e}",
                request,
                data={"payload": payload},
                status_code=STATUS_ERROR,
                exception=e,
            ) from e

        return messages

    def make_error_response(
        self,
        request: Request,
        envelope: ErrorDetails,
        warnings: list[ErrorDetails] | None = None,
    ) -> Response:
        """Construct an error response with appropriate error payload.

        Canonical rendering policy: the system ``--error`` route (a regular
        route returning a ``Page``, overridable via
        ``configuration.system_routes``) is the canonical error rendering
        path. ``SimpleErrorPage`` is the last-resort fallback when the error
        route itself fails; the ``ErrorPage`` payload class is not used here.

        Args:
            request: Associated request for context and URL.
            envelope: Canonical envelope describing the failure.
            warnings: Request-scoped warnings to attach to the response.

        Returns:
            Response: Error response ready to send to the client.
        """
        from drafter.router.system_routes import _SYSTEM_ERROR_ROUTE

        try:
            configuration = self.get_current_configuration()
            error_handler = self.router.get_route(_SYSTEM_ERROR_ROUTE)
            if error_handler is None:
                raise Exception(
                    f"No error handler registered for {_SYSTEM_ERROR_ROUTE} route"
                )
            error_payload = error_handler(self.state, envelope, self)
            body = error_payload.render(self.state, configuration)
        except Exception as e:
            error_page_envelope = envelope_from_exception(
                e,
                "system.error_page_failed",
                CATEGORY_SYSTEM,
                message="Failed to create ErrorPage payload",
                details=(
                    f"Original error: {repr(envelope)}\n"
                    f"Error during ErrorPage creation: {repr(e)}"
                ),
                context=Correlation(
                    route=request.url, request_id=request.id, phase="visit"
                ),
                status_code=STATUS_ERROR,
            )
            log_error(error_page_envelope, "client_server.make_error_response")
            simpler_error_payload = SimpleErrorPage(error_page_envelope.message)
            response = Response(
                id=self.response_count,
                request_id=request.id,
                payload=simpler_error_payload,
                url=request.url,
                status_code=STATUS_ERROR,
                body=simpler_error_payload.render(self.state, None),
                message=error_page_envelope.message,
                errors=[envelope, error_page_envelope],
                warnings=list(warnings) if warnings else [],
            )
        else:
            response = Response(
                id=self.response_count,
                request_id=request.id,
                body=body,
                url=request.url,
                payload=error_payload,
                status_code=envelope.status_code or STATUS_ERROR,
                message=envelope.message,
                errors=[envelope],
                warnings=list(warnings) if warnings else [],
            )
        log_record(
            ResponseEvent.from_response(response, "", self.check_timer()),
            "client_server.make_error_response",
            route=request.url,
            request_id=request.id,
            response_id=response.id,
        )
        self.response_count += 1
        self.transition("committing")
        return response

    def add_route(self, url: str, func: Any, is_system_route=False) -> None:
        """Register a new route handler in the router.

        Args:
            url: Route URL path.
            func: Handler function to call for this route.
            is_system_route: Whether the route is registered by the
                framework itself rather than user code; recorded on the
                logged `RouteAddedEvent`.
        """
        # TODO: Inspect route function for valid signature.
        details = self.router.add_route(url, func)
        log_record(
            RouteAddedEvent(**details, is_system_route=is_system_route),
            "client_server.add_route",
        )

    def format_simple_site_error(self, envelope) -> InitialSiteData:
        """Format a simple HTML error message for site rendering failures.

        Args:
            envelope: The error details envelope to display.

        Returns:
            `InitialSiteData` from the site's error fallback renderer, or,
            if that renderer itself fails, a minimal hard-coded error page
            showing both the original envelope and the rendering error.
        """
        try:
            return self.site.render_error_fallback(envelope)
        except Exception as e:
            return InitialSiteData(
                site_html=f"""
        <div>
            <h1>System Error</h1>
            <p>We encountered the following major system error while setting up the site. Details:</p>
            <pre style='white-space: pre-wrap;'>{repr(envelope)}</pre>
            <p>Additionally, an error occurred while trying to render the error message:</p>
            <pre style='white-space: pre-wrap;'>{repr(e)}</pre>
            <p>Please share this information with the developers to help us fix this issue. We apologize for the inconvenience.</p>
        </div>""",
                site_title="System Error (Fallback Level 2)",
                error=True,
                framed=True,
            )

    def do_configuration(self) -> InitialSiteData | None:
        """Apply dynamic configuration to the site.

        Returns:
            Optional[InitialSiteData]: None on success, or fallback error
            site data if configuration processing fails.
        """
        self.transition("configuring")
        try:
            configuration = self.process_dynamic_configuration()
        except Exception as e:
            envelope = envelope_from_exception(
                e,
                "site.processing_failed",
                CATEGORY_SYSTEM,
                message="Failed to process default site configuration",
                details=f"Original exception: {e}",
            )
            log_error(
                envelope,
                "client_server.render_site",
            )
            return self.format_simple_site_error(envelope)
        log_record(
            InitialConfigurationEvent(config=configuration.to_json()),
            "client_server.do_configuration",
        )
        return None

    def do_render(self) -> InitialSiteData:
        """Render the initial site HTML framing structure.

        Creates the DOM structure with frame, header, body, footer, form,
        and debug panel layout.

        Returns:
            InitialSiteData: Rendered HTML and metadata, or error data if rendering fails.
        """
        self.transition("rendering")
        try:
            site = self.site.render()
            log_error(
                ErrorDetails(
                    id="site.rendered",
                    category=CATEGORY_SYSTEM,
                    message="Initial site HTML rendered",
                    severity=SEVERITY_INFO,
                    details=f"Site HTML: {site}",
                ),
                "client_server.render_site",
            )
        except Exception as e:
            envelope = envelope_from_exception(
                e,
                "site.rendering_failed",
                CATEGORY_SYSTEM,
                message="Failed to render initial site HTML",
                details=f"Original exception: {e}",
            )
            log_error(
                envelope,
                "client_server.render_site",
            )
            # TODO: Clean this nested error template up a little bit
            return self.format_simple_site_error(envelope)
        return site

    def do_finish_visit(self):
        """Transition the server to the idle phase, allowing it to receive requests."""
        self.transition("idle")

    def do_listen_for_events(self, handler: Any) -> Subscription:
        """Subscribe a handler to all events on the event bus.

        Args:
            handler: Callable to invoke on any event.

        Returns:
            The bus subscription, so the caller that wired the handler can
            unsubscribe it when the instance is discarded.
        """
        # self.monitor.register_listener(handler)
        subscription = self.event_bus.subscribe("*", handler)
        self.event_bus.process_unprocessed_events()
        return subscription

    def get_default_configuration(self) -> ClientServerConfiguration:
        """Return the shared default server configuration instance.

        Note that this is the system-wide default configuration itself, not
        a copy; mutations affect all servers sharing the interpreter.

        Returns:
            ClientServerConfiguration: The shared default configuration instance.
        """
        system = get_system_configuration()
        return system.client_server

    def get_current_configuration(self) -> ClientServerConfiguration:
        """Return the current active server configuration.

        Returns:
            ClientServerConfiguration: Current configuration instance from the site.
        """
        return self.site.get_configuration()

    def get_current_request_id(self) -> int | None:
        """Return the ID of the request currently being processed.

        Returns:
            Optional[int]: Current request ID, or None if not processing a request.
        """
        current_request = self.requests.get_current()
        return current_request.id if current_request is not None else None

    def precompile_server(self, initial_state: Any) -> tuple[str, str]:
        """Precompile initial page render for faster loading.

        Executes the index route to generate precompiled HTML body and headers.

        Args:
            initial_state: Initial application state.

        Returns:
            Tuple of (compiled_body, compiled_headers) as strings.
        """
        initial_site = self.do_render()
        self.do_start(initial_state=initial_state)
        initial_request = Request("precompilation", "index", {}, {}, "")
        response = self.do_visit(initial_request)
        # TODO: Extract compiled body and headers
        body = response.body or "Error during precompilation."
        headers = initial_site.additional_css
        compiled_headers = "\n".join(
            [
                header.precompile_to_html({DRAFTER_TAG_CLASSES["PRECOMPILE_HEADERS"]})
                for header in headers
            ]
        )

        return body, compiled_headers
