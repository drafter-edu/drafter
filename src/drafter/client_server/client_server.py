from dataclasses import dataclass
from typing import Any, Callable, Literal, Optional, List, Tuple, Union, Dict
import time

from drafter.client_server.context import Scope
from drafter.client_server.errors import VisitError
from drafter.data.channel import Message
from drafter.history.state import SiteState
from drafter.monitor.bus import EventBus
from drafter.monitor.events.config import (
    InitialConfigurationEvent,
    ResetServerEvent,
    ServerInitializedEvent,
    UpdatedConfigurationEvent,
)
from drafter.monitor.events.errors import DrafterError
from drafter.monitor.events.request import (
    RequestEvent,
    RequestParseEvent,
    ResponseEvent,
)
from drafter.monitor.events.routes import RouteAddedEvent
from drafter.monitor.events.state import UpdatedStateEvent
from drafter.monitor.telemetry import TelemetryCorrelation, TelemetryEvent
from drafter.payloads.kinds.error_page import ErrorPage, SimpleErrorPage
from drafter.payloads.payloads import ResponsePayload
from drafter.data.request import Request
from drafter.data.response import Response
from drafter.payloads.verification import (
    verify_page_state_history,
    verify_response_payload_type,
)
from drafter.router.routes import Router
from drafter.monitor.audit import log_error, log_warning, log_info, log_data
from drafter.site.initial_site_data import InitialSiteData
from drafter.site.site import Site
from drafter.config.client_server import ClientServerConfiguration
from drafter.payloads.target import Target


ServerPhases = Union[
    Literal["initializing"],
    Literal["initialized"],
    Literal["configuring"],
    Literal["rendering"],
    Literal["starting"],
    Literal["started"],
    Literal["visiting"],
    Literal["committing"],
    Literal["idle"],
]


@dataclass
class ClientServer:
    """
    The ClientServer is responsible for handling requests from the BridgeClient,
    routing them to the appropriate functions, and returning responses.

    The Server can be in one of the following phases:
    - initializing: During the initial ClientServer constructor call
    - initialized: After the constructor has completed, but before the `start` method is called
    - starting: During the execution of the `start` method
    - configuring: During the processing of static and dynamic configuration
    - rendering: During the rendering of the initial site into its HTML meta-structure (NOT the student's page content)
    - started: After the `start` method has completed, but before the first request is processed
    - visiting: After the first request is processed, and the server is fully operational
    - committing: During the process of committing changes or updates from the response.
    - idle: When the server is not processing a request, but is still running and can receive requests. This is the default state of the server after it has started and is waiting for requests.

    TODO: Ability to override ErrorPage rendering with custom error pages.

    Attributes:
        custom_name: A custom name for the server, useful for debugging.
        router: The Router instance that handles URL routing.
        state: The state information about the student's site.
        response_count: A counter for the number of responses made, used to assign unique IDs.
        logger: An AuditLogger instance for logging errors, warnings, and info.
        monitor: A Monitor instance for tracking telemetry data.
        configuration: The ClientServerConfiguration instance for server settings.
    """

    custom_name: str
    state: SiteState
    _default_configuration: ClientServerConfiguration
    phase: ServerPhases = "initializing"
    started: bool = False

    def __init__(self, custom_name: str) -> None:
        self.custom_name = custom_name
        self.event_bus = EventBus()
        
        server_initialized_event = ServerInitializedEvent()
        self.event_bus.publish(
            TelemetryEvent(
                event_type=server_initialized_event.event_type,
                data=server_initialized_event,
                correlation=TelemetryCorrelation(),
                source="client_server.server_initialized",
            )
        )
        self.site = Site()
        self.router = Router()
        self.state = SiteState()
        self._default_configuration = ClientServerConfiguration()
        self.response_count = 0

        self.requests = Scope()
        self.start_time = 0.0
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
        log_data(
            ResetServerEvent(),
            "client_server.reset",
        )
        # log_info(
        #     "server.reset",
        #     "Resetting ClientServer to initial state",
        #     "client_server.reset",
        #     f"Server name: {self.custom_name}",
        # )
        
    def transition(self, new_phase: ServerPhases):
        """Transition the server to a new phase.

        Args:
            new_phase: The new phase to transition to.
        """
        self.phase = new_phase

    def process_static_configuration(self, command_line_arguments=None):
        """Process and merge static configuration from multiple sources.

        Configuration sources are merged in precedence order:
        1. Code defaults
        2. Environment variables
        3. Command line arguments
        4. Configuration file (if specified)

        The result becomes the default configuration.

        Args:
            command_line_arguments: Optional CLI arguments to process.

        TODO:
            Finish implementation.
        """
        # TODO: Finish this

    def process_dynamic_configuration(self, extra_configuration):
        """Initialize runtime configuration from defaults with extra updates.

        Separates default and current configurations so runtime changes
        don't affect defaults. Call only during server startup.

        Args:
            extra_configuration: Configuration overrides to apply.

        Returns:
            ClientServerConfiguration: The applied configuration.
        """
        self._default_configuration.update_multiple_configuration(**extra_configuration)
        configuration = self.get_default_configuration()
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
                    self._default_configuration.update_configuration(key, value)
            else:
                self._default_configuration.update_configuration(key, value)
            log_data(
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
            return getattr(self._default_configuration, key)

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
                log_info(
                    "state.initialized",
                    "Initializing server state",
                    "client_server.start",
                    f"Initial state: {repr(initial_state)}",
                )
            except Exception as e:
                log_error(
                    "state.initialization_failed",
                    "Failed to initialize server state",
                    "client_server.start",
                    f"Initial state: {repr(initial_state)}",
                    exception=e,
                )
        # Register any default routes, if needed
        self.register_system_routes()
        # All done!
        self.transition("started")
        self.started = True
        log_info(
            "server.started",
            "Started ClientServer",
            "client_server.start",
            f"Server name: {self.custom_name}",
        )

    def register_system_routes(self):
        """Register system routes like --error, --about, --reset.

        Args:
            routes: Mapping of route names to handler callables.

        TODO:
            Finish implementation.
        """
        from drafter.router.system_routes import _SYSTEM_ROUTES

        configuration = self.get_current_configuration()
        for route, default_handler in _SYSTEM_ROUTES.items():
            route_handler = configuration.system_routes.get(route) or default_handler
            if not self.router.has_route(route):
                self.add_route(route, route_handler, True)

    def get_route(self, request: Request):
        """Resolve a request URL to a route handler function.

        Args:
            request: Request with URL to resolve.

        Returns:
            Callable: The route handler function.

        Raises:
            VisitError: If no route matches the URL (404).
        """
        route_func = self.router.get_route(request.url)
        if route_func is None:
            raise VisitError(
                log_error(
                    "request.route_not_found",
                    f"No route found for URL: {request.url}",
                    "client_server.visit",
                    repr(request),
                    route=request.url,
                    request_id=request.id,
                ),
                404,
            )
        return route_func

    def _get_extra_dependencies(
        self, request: Request, configuration: ClientServerConfiguration
    ) -> dict[str, Any]:
        """Get extra dependencies to inject into route handlers.

        Returns:
            dict: Mapping of dependency names to instances.
        """
        return {
            "_server": self,
            "_configuration": configuration,
            "_request": request,
        }

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
            VisitError: On argument parsing or execution failures.
        """
        # Call the route function to get the payload
        try:
            args, kwargs, representation = self.router.prepare_arguments(
                request,
                self.state.current,
                configuration,
                self._get_extra_dependencies(request, configuration),
            )
            log_data(
                RequestParseEvent(
                    request_id=request.id,
                    representation=representation,
                ),
                "client_server.execute_route",
                route=request.url,
                request_id=request.id,
            )
        except Exception as e:
            raise VisitError(
                log_error(
                    "request.argument_parsing_failed",
                    f"Error while parsing arguments for request to URL {request.url}: {e}",
                    "client_server.visit",
                    repr(request),
                    route=request.url,
                    exception=e,
                ),
                400,
            )
        try:
            return route_func(*args, **kwargs), representation
        except Exception as e:
            raise VisitError(
                log_error(
                    "request.route_execution_failed",
                    f"Error while processing request for URL {request.url}: {e}",
                    "client_server.visit",
                    repr(request),
                    route=request.url,
                    exception=e,
                ),
                500,
            )

    def verify_payload(
        self, request: Request, payload: Any, configuration: ClientServerConfiguration
    ):
        """Validate payload type and payload-specific rules.

        Args:
            request: Associated request for error context.
            payload: Payload to verify.
            configuration: Current server configuration.

        Raises:
            VisitError: If payload verification fails.
        """
        # Check that it's a valid payload type
        possible_incorrect_type = verify_response_payload_type(request, payload)
        if possible_incorrect_type is not None:
            raise VisitError(
                log_error(
                    "request.payload_verification_failed",
                    f"Payload verification failed for URL {request.url}: {possible_incorrect_type}",
                    "client_server.visit",
                    f"Request: {repr(request)}\nPayload: {repr(payload)}",
                    route=request.url,
                ),
                501,
            )
        # Payload specific verification
        try:
            payload.verify(self.router, self.state, configuration, request)
        except Exception as e:
            raise VisitError(
                log_error(
                    "request.payload_verification_failed",
                    f"Payload verification failed for URL {request.url}: {e}",
                    "client_server.visit",
                    f"Request: {repr(request)}\nPayload: {repr(payload)}",
                    route=request.url,
                    exception=e,
                ),
                502,
            )

    def render_payload(
        self,
        request: Request,
        payload: ResponsePayload,
        configuration: ClientServerConfiguration,
    ) -> Optional[str]:
        """Render a payload to HTML string.

        Args:
            request: Associated request for error context.
            payload: Payload to render.
            configuration: Current server configuration.

        Returns:
            str or None: HTML output of the rendered payload.

        Raises:
            VisitError: If rendering fails.
        """
        # Render the payload
        try:
            return payload.render(self.state, configuration)
        except Exception as e:
            raise VisitError(
                log_error(
                    "request.payload_rendering_failed",
                    f"Error while rendering payload for URL {request.url}: {e}",
                    "client_server.visit",
                    f"Request: {repr(request)}\nPayload: {repr(payload)}",
                    route=request.url,
                    exception=e,
                ),
                503,
            )

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
            VisitError: If formatting fails.
        """
        # Format the payload for display in the history panel
        try:
            return payload.format(self.state, representation, configuration)
        except Exception as e:
            raise VisitError(
                log_error(
                    "request.payload_formatting_failed",
                    f"Error while formatting payload for URL {request.url}: {e}",
                    "client_server.visit",
                    f"Request: {repr(request)}\nPayload: {repr(payload)}",
                    route=request.url,
                    exception=e,
                ),
                509,
            )

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
            VisitError: If state verification or update fails.
        """
        is_updated, updated_state = payload.get_state_updates()
        if is_updated:
            # Check that the state update will be valid
            possible_state_update_issue = verify_page_state_history(
                request, updated_state, self.state.history
            )
            if possible_state_update_issue is not None:
                raise VisitError(
                    log_error(
                        "request.payload_verification_failed",
                        f"Payload verification failed for URL {request.url}: {possible_state_update_issue}",
                        "client_server.visit",
                        f"Request: {repr(request)}\nPayload: {repr(payload)}",
                        route=request.url,
                    ),
                    501,
                )
            try:
                self.state.update(updated_state)
                log_data(
                    UpdatedStateEvent.from_state(updated_state),
                    "client_server.handle_state_updates",
                    request_id=request.id,
                    route=request.url,
                )
            except Exception as e:
                raise VisitError(
                    log_error(
                        "state.update_failed",
                        "Failed to update server state from payload",
                        "client_server.handle_state_updates",
                        f"Updated state: {repr(updated_state)}",
                        exception=e,
                    ),
                    403,
                )

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

        Args:
            request: The request to process.

        Returns:
            Response: Success or error response to send to the client.
        """
        self.start_timer()
        self.transition("visiting")
        log_data(
            RequestEvent.from_request(request),
            "client_server.visit",
            route=request.url,
            request_id=request.id,
        )
        with self.requests.push(request):
            try:
                # TODO: Most of these should be private methods
                configuration = self.get_current_configuration()
                route_func = self.get_route(request)
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
            except VisitError as ve:
                return self.make_error_response(
                    request, ve.error, status_code=ve.status_code
                )

            # Return successfully
            try:
                response = self.make_success_response(
                    request.id, request.url, body, payload, messages, target
                )
            except Exception as e:
                return self.make_error_response(
                    request,
                    log_error(
                        "response.creation_failed",
                        f"Failed to create success response for URL {request.url}: {e}",
                        "client_server.visit",
                        f"Request: {repr(request)}",
                        route=request.url,
                        exception=e,
                    ),
                    504,
                )
            log_data(
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

    def make_success_response(
        self,
        request_id: int,
        url: str,
        body: Optional[str],
        payload: ResponsePayload,
        messages: List[Message],
        target: Optional[Target],
    ) -> Response:
        """Construct a successful response from request processing results.

        Args:
            request_id: ID of the associated request.
            url: URL that was processed.
            body: Rendered HTML body content.
            payload: ResponsePayload that generated the body.
            messages: Channel messages to execute on the client.
            target: Optional target selector for fragment updates.

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
        )
        response.send_messages(messages)
        self.response_count += 1

        return response

    def get_target(
        self,
        request: Request,
        payload: ResponsePayload,
        configuration: ClientServerConfiguration,
    ) -> "Optional[Target]":
        """Extract the Target object from a payload.

        Args:
            request: Associated request for error context.
            payload: Payload to extract target from.
            configuration: Current server configuration.

        Returns:
            Optional[Target]: Target object (e.g., for Fragment updates).

        Raises:
            VisitError: If target retrieval fails.
        """
        try:
            return payload.get_target(request)
        except Exception as e:
            raise VisitError(
                log_error(
                    "request.payload_target_retrieval_failed",
                    f"Error while retrieving target from payload for URL {request.url}: {e}",
                    "client_server.visit",
                    f"Request: {repr(request)}\nPayload: {repr(payload)}",
                    route=request.url,
                    exception=e,
                ),
                505,
            )
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
            VisitError: If message retrieval fails.
        """
        try:
            messages = payload.get_messages(self.state, configuration)
            if messages is None:
                messages = []
        except Exception as e:
            raise VisitError(
                log_error(
                    "request.payload_message_retrieval_failed",
                    f"Error while retrieving messages from payload for URL {request.url}: {e}",
                    "client_server.visit",
                    f"Request: {repr(request)}\nPayload: {repr(payload)}",
                    route=request.url,
                    exception=e,
                ),
                510,
            )

        return messages

    def make_error_response(
        self,
        request: Request,
        error: DrafterError,
        status_code: int = 500,
    ) -> Response:
        """Construct an error response with appropriate error payload.

        Attempts to render a full ErrorPage; falls back to SimpleErrorPage
        if that fails.

        Args:
            request: Associated request for context and URL.
            error: Domain error to report.
            status_code: HTTP-like status code for the error.

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
            error_payload = error_handler(self.state, error, self)
            body = error_payload.render(self.state, configuration)
            # error_payload = ErrorPage(error)
            # body = error_payload.render(self.state, configuration)
        except Exception as e:
            error_page_error = log_error(
                "error_page.creation_failed",
                "Failed to create ErrorPage payload",
                "client_server.make_error_response",
                f"Original error: {repr(error)}\nError during ErrorPage creation: {repr(e)}",
                route=request.url,
                exception=e,
            )
            simpler_error_payload = SimpleErrorPage(error_page_error.message)
            response = Response(
                id=self.response_count,
                request_id=request.id,
                payload=simpler_error_payload,
                url=request.url,
                status_code=500,
                body=simpler_error_payload.render(self.state, None),
                message=error_page_error.message,
                errors=[error, error_page_error],
            )
        else:
            response = Response(
                id=self.response_count,
                request_id=request.id,
                body=body,
                url=request.url,
                payload=error_payload,
                status_code=status_code,
                message=error.message,
                errors=[error],
            )
        log_data(
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

        TODO:
            Inspect route function for valid signature.
        """
        self.router.add_route(url, func)
        log_data(
            RouteAddedEvent(
                url=url,
                signature=self.router.signatures[url].to_string(),
                is_system_route=is_system_route,
            ),
            "client_server.add_route",
        )

    def do_configuration(self, extra_configuration) -> Optional[InitialSiteData]:
        """Apply dynamic configuration and return initial site data.

        Args:
            extra_configuration: Configuration overrides to apply.

        Returns:
            Optional[InitialSiteData]: Site HTML and metadata, or error data if configuration fails.
        """
        self.transition("configuring")
        try:
            configuration = self.process_dynamic_configuration(extra_configuration)
        except Exception as e:
            error = log_error(
                "site.processing_failed",
                "Failed to process default site configuration",
                "client_server.render_site",
                f"Original exception: {e}",
                exception=e,
            )
            site = f"<div><h1>Error processing site configuration</h1><p>{error.message}</p></div>"
            return InitialSiteData(site_html=site, site_title="Error", error=True)
        log_data(
            InitialConfigurationEvent(config=configuration.to_json()),
            "client_server.do_configuration",
        )

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
            log_info(
                "site.rendered",
                "Initial site HTML rendered",
                "client_server.render_site",
                f"Site HTML: {site}",
            )
        except Exception as e:
            error = log_error(
                "site.rendering_failed",
                "Failed to render initial site HTML",
                "client_server.render_site",
                f"Original exception: {e}",
                exception=e,
            )
            site = f"<div><h1>Error rendering site</h1><p>{error.message}</p></div>"
            return InitialSiteData(site_html=site, site_title="Error", error=True)
        return site
    
    def do_finish_visit(self):
        """Transition the server to the idle phase, allowing it to receive requests."""
        self.transition("idle")
    

    def do_listen_for_events(self, handler: Any) -> None:
        """Subscribe a handler to all events on the event bus.

        Args:
            handler: Callable to invoke on any event.
        """
        # self.monitor.register_listener(handler)
        self.event_bus.subscribe("*", handler)
        self.event_bus.process_unprocessed_events()

    def get_default_configuration(self) -> ClientServerConfiguration:
        """Return a copy of the default server configuration.

        Returns:
            ClientServerConfiguration: Default configuration instance.
        """
        return self._default_configuration.copy()

    def get_current_configuration(self) -> ClientServerConfiguration:
        """Return the current active server configuration.

        Returns:
            ClientServerConfiguration: Current configuration instance from the site.
        """
        return self.site.get_configuration()

    def get_current_request_id(self) -> Optional[int]:
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
            server: The ClientServer instance.
            config: AppServer configuration.
            initial_state: Initial application state.

        Returns:
            Tuple of (compiled_body, compiled_headers) as strings.
        """
        self.do_start(initial_state=initial_state)
        initial_request = Request(-1, "precompilation", "index", {}, {}, "")
        response = self.do_visit(initial_request)
        # TODO: Extract compiled body and headers
        body = response.body or "Error during precompilation."

        return body, ""
