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


ServerPhases = Union[
    Literal["initializing"],
    Literal["initialized"],
    Literal["starting"],
    Literal["configuring"],
    Literal["rendering"],
    Literal["started"],
    Literal["running"],
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
    - running: After the first request is processed, and the server is fully operational
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
        self.site = Site()
        self.router = Router()
        self.state = SiteState()
        self._default_configuration = ClientServerConfiguration()
        self.response_count = 0

        self.requests = Scope()
        self.start_time = 0.0
        self.phase = "initialized"

    def reset(self) -> None:
        """
        Resets the server to its initial state.
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

    def process_static_configuration(self, command_line_arguments=None):
        """
        Processes static configuration from various sources and merges them together.

        The configuration is determined by merging the following sources together, in order of precedence (later items override earlier ones):
        1. Defaults defined in the code
        2. Environment variables
        3. Command line arguments
        4. A configuration file (provided by either 1. the environment variables, or 2. command line arguments)

        The resulting merged configuration becomes the default configuration for the server.

        Args:
            command_line_arguments: The command line arguments to process for configuration.
        """
        # TODO: Finish this

    def process_dynamic_configuration(self, extra_configuration):
        """
        Copies the default configuration to the site's current configuration.
        These will be separate objects, so that changes to the current configuration during runtime
        do not affect the default configuration.

        Note that this should only be called during server startup. Calling
        this subsequently will not modify the actively running site in any immediately visible way.
        """
        self._default_configuration.update_multiple_configuration(**extra_configuration)
        configuration = self.get_default_configuration()
        self.site.set_configuration(configuration)
        return configuration

    def reconfigure(self, update_default: bool = False, **kwargs):
        """
        Updates the server configuration with new values.

        Args:
            update_default: If True, also updates the default configuration with the new value.
            kwargs: The configuration keys and their new values to update.
        """
        for key, value in kwargs.items():
            self.site.update_configuration(key, value)
            if update_default:
                self._default_configuration.update_configuration(key, value)
            log_data(
                UpdatedConfigurationEvent(
                    key=key, value=value, update_default=update_default
                ),
                "client_server.reconfigure",
                request_id=self.get_current_request_id(),
            )

    def get_config_setting(self, key: str):
        # TODO: Check for non-existent keys and raise an error
        if self.started:
            return getattr(self.site._configuration, key)
        else:
            return getattr(self._default_configuration, key)

    def reconfigure_flip(self, key: str):
        current_value = self.get_config_setting(key)
        self.reconfigure(**{key: not current_value})

    def do_start(self, initial_state: Any = None) -> None:
        """
        Starts the server with the given initial state.

        Args:
            initial_state: The initial state to set for the server.
        """
        self.phase = "starting"
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
        self.router.register_default_routes(
            lambda state: self.default_reset_function(state),
            lambda state: self.default_about_function(state),
        )
        # All done!
        self.phase = "started"
        self.started = True
        log_info(
            "server.started",
            "Started ClientServer",
            "client_server.start",
            f"Server name: {self.custom_name}",
        )

    def register_system_routes(self, routes: dict[str, Optional[Callable]]):
        # TODO: Finish this
        """
        --error
        --about
        --reset
        """
        pass

    def default_reset_function(self, state):
        from drafter.payloads.kinds.redirect import Redirect

        self.state.reset()
        return Redirect("index")

    def default_about_function(self, state):
        from drafter.payloads.kinds.page import Page

        # TODO: Move this elsewhere
        # TODO: Should use the student's site information if available
        about_content = """
        <h1>About Drafter</h1>
        <p>Drafter is an educational library for building simple web applications using Python.</p>
        <p>Version: 2.0.0</p>
        <p>For more information, visit our <a href="https://drafter-edu.github.io/drafter/" target="_blank">website</a>.</p>
        """
        return Page(state, [about_content])

    def get_route(self, request: Request):
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

    def execute_route(
        self, route_func, request: Request, configuration: ClientServerConfiguration
    ) -> tuple[Any, str]:
        # Call the route function to get the payload
        try:
            args, kwargs, representation = self.router.prepare_arguments(
                request, self.state.current, configuration
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
        # print(args, kwargs, representation)
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
        self.start_time = time.time()

    def check_timer(self) -> float:
        return (time.time() - self.start_time) * 1000  # in milliseconds

    def do_visit(self, request: Request) -> Any:
        """
        Uses the information in the request to find and call the appropriate route function.

        Args:
            request: The request to process.

        Returns:
            The result of the route function.
        """
        self.start_timer()
        self.phase = "running"
        log_data(
            RequestEvent.from_request(request),
            "client_server.visit",
            route=request.url,
            request_id=request.id,
        )
        with self.requests.push(request):
            try:
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
            self.phase = "idle"
            return response

    def make_success_response(
        self,
        request_id: int,
        url: str,
        body: Optional[str],
        payload: ResponsePayload,
        messages: List[Message],
        target: Optional[str],
    ) -> Response:
        """
        Makes a successful response for the server with the given page.

        Args:
            request_id: The ID of the request.
            body: The rendered body content.
            payload: The payload to include in the response.
            messages: A list of messages to include in the response.

        Returns:
            The response from the server.
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
    ) -> Optional[str]:
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
        """
        Makes an error response for the server with the given message and status code.

        Args:
            message: The error message to include in the response.
            status_code: The HTTP status code for the error.

        Returns:
            The error response from the server.
        """
        try:
            configuration = self.get_current_configuration()
            error_payload = ErrorPage(error)
            body = error_payload.render(self.state, configuration)
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
        return response

    def add_route(self, url: str, func: Any) -> None:
        """
        Adds a new route to the server.

        TODO: Inspect that the route has a valid route signature.

        Args:
            url: The URL to add the route to.
            func: The function to call when the route is accessed.
        """
        self.router.add_route(url, func)
        log_data(
            RouteAddedEvent(url=url, signature=self.router.signatures[url].to_string()),
            "client_server.add_route",
        )

    def do_configuration(self, extra_configuration) -> Optional[InitialSiteData]:
        self.phase = "configuring"
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
        print(
            "Site configuration processed successfully", self.site.get_configuration()
        )

    def do_render(self) -> InitialSiteData:
        """
        Renders the initial site HTML. This is called to create the site
        framing structure that includes the frame, header, body, footer, form, and
        debug info.

        Returns:
            The rendered HTML of the initial site.
        """
        self.phase = "rendering"
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

    def do_listen_for_events(self, handler: Any) -> None:
        """
        Registers a listener to the monitor.

        Args:
            handler: The handler function to register.

        Returns:
            None
        """
        # self.monitor.register_listener(handler)
        self.event_bus.subscribe("*", handler)
        self.event_bus.process_unprocessed_events()

    def get_default_configuration(self) -> ClientServerConfiguration:
        """
        Returns the default configuration for the client server.

        Returns:
            The default ClientServerConfiguration instance.
        """
        return self._default_configuration.copy()

    def get_current_configuration(self) -> ClientServerConfiguration:
        """
        Returns the current configuration for the client server.

        Returns:
            The current ClientServerConfiguration instance.
        """
        return self.site.get_configuration()

    def get_current_request_id(self) -> Optional[int]:
        """
        Returns the ID of the current request being processed, if any.

        Returns:
            The current request ID, or None if no request is being processed.
        """
        current_request = self.requests.get_current()
        return current_request.id if current_request is not None else None
