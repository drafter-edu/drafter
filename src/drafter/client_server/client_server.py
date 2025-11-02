from dataclasses import dataclass
from typing import Any, Optional, List, Tuple, Union, Dict

from drafter.client_server.context import Scope
from drafter.client_server.errors import VisitError
from drafter.history.state import SiteState
from drafter.data.errors import DrafterError
from drafter.monitor.bus import EventBus
from drafter.monitor.monitor import Monitor
from drafter.payloads import Page
from drafter.payloads.error_page import ErrorPage, SimpleErrorPage
from drafter.payloads.payloads import ResponsePayload
from drafter.data.request import Request
from drafter.data.response import Response
from drafter.router.routes import Router
from drafter.audit import log_error, log_warning, log_info
from drafter.site import Site
from drafter.config.client_server import ClientServerConfiguration


@dataclass
class ClientServer:
    """
    The ClientServer is responsible for handling requests from the BridgeClient,
    routing them to the appropriate functions, and returning responses.

    TODO: Ability to override ErrorPage rendering with custom error pages.

    :ivar custom_name: A custom name for the server, useful for debugging.
    :ivar router: The Router instance that handles URL routing.
    :ivar state: The state information about the student's site.
    :ivar response_count: A counter for the number of responses made, used to assign unique IDs.
    :ivar logger: An AuditLogger instance for logging errors, warnings, and info.
    :ivar monitor: A Monitor instance for tracking telemetry data.
    :ivar configuration: The ClientServerConfiguration instance for server settings.
    """

    custom_name: str
    state: SiteState
    configuration: ClientServerConfiguration

    def __init__(self, custom_name: str) -> None:
        self.custom_name = custom_name
        self.site = Site()
        self.router = Router()
        self.state = SiteState()
        self.monitor = Monitor()
        self.configuration = ClientServerConfiguration()
        self.response_count = 0

        self.requests = Scope()

        self.process_configuration()

    def process_configuration(self):
        self.site.title = self.configuration.site_title

    def start(self, initial_state: Any = None) -> None:
        """
        Starts the server with the given initial state.

        :param initial_state: The initial state to set for the server.
        """
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
        log_info(
            "server.started",
            "Starting ClientServer",
            "client_server.start",
            f"Server name: {self.custom_name}",
        )

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
                ),
                404,
            )
        return route_func

    def execute_route(self, route_func, request: Request) -> Any:
        # Call the route function to get the payload
        try:
            args, kwargs, representation = self.router.prepare_arguments(
                request, self.state.current
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
        print(args, kwargs, representation)
        try:
            return route_func(*args, **kwargs)
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

    def verify_payload(self, request: Request, payload: Any):
        if not isinstance(payload, ResponsePayload):
            page_type_name = type(payload).__name__
            raise VisitError(
                log_error(
                    "request.invalid_route_response",
                    f"Route function for URL {request.url} did not return a Page. Instead got: {page_type_name}",
                    "client_server.visit",
                    f"Request: {repr(request)}\nPage: {repr(payload)}",
                    route=request.url,
                ),
                501,
            )

    def render_payload(self, request: Request, payload: ResponsePayload) -> str:
        # Render the payload
        try:
            return payload.render(self.state, self.configuration)
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
                502,
            )

    def handle_state_updates(self, payload: ResponsePayload) -> None:
        is_updated, updated_state = payload.get_state_updates()
        if is_updated:
            try:
                self.state.update(updated_state)
                log_info(
                    "state.updated",
                    "Updating server state from payload",
                    "client_server.handle_state_updates",
                    f"Updated state: {repr(updated_state)}",
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

    def visit(self, request: Request) -> Any:
        """
        Uses the information in the request to find and call the appropriate route function.

        :param request: The request to process.
        :return: The result of the route function.
        """
        log_info(
            "request.received",
            f"Request received: {request}",
            "client_server.visit",
            repr(request),
            route=request.url,
        )
        with self.requests.push(request):
            try:
                route_func = self.get_route(request)
                payload = self.execute_route(route_func, request)
                self.verify_payload(request, payload)
                body = self.render_payload(request, payload)
                self.handle_state_updates(payload)
            except VisitError as ve:
                return self.make_error_response(
                    request, ve.error, status_code=ve.status_code
                )

        # Return successfully
        response = self.make_success_response(request.id, body, payload)
        log_info(
            "response.created",
            f"Response created for request ID {request.id}",
            "client_server.visit",
            f"Response: {repr(response)}",
            route=request.url,
        )
        return response

    def make_success_response(
        self, request_id: int, body: str, payload: ResponsePayload
    ) -> Response:
        """
        Makes a successful response for the server with the given page.

        :param page: The page to include in the response.
        :return: The response from the server.
        """
        response = Response(
            id=self.response_count,
            request_id=request_id,
            payload=payload,
            body=body,
        )
        self.response_count += 1
        return response

    def make_error_response(
        self, request: Request, error: DrafterError, status_code: int = 500
    ) -> Response:
        """
        Makes an error response for the server with the given message and status code.

        :param message: The error message to include in the response.
        :param status_code: The HTTP status code for the error.
        :return: The error response from the server.
        """
        try:
            error_payload = ErrorPage(error)
            body = error_payload.render(self.state, self.configuration)
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
            return Response(
                id=self.response_count,
                request_id=request.id,
                payload=simpler_error_payload,
                status_code=500,
                body=simpler_error_payload.render(self.state, self.configuration),
                message=error_page_error.message,
                errors=[error, error_page_error],
            )
        response = Response(
            id=self.response_count,
            request_id=request.id,
            body=body,
            payload=error_payload,
            status_code=status_code,
            message=error.message,
            errors=[error],
        )
        self.response_count += 1
        return response

    def add_route(self, url: str, func: Any) -> None:
        """
        Adds a new route to the server.

        TODO: Inspect that the route has a valid route signature.

        :param url: The URL to add the route to.
        :param func: The function to call when the route is accessed.
        """
        self.router.add_route(url, func)
        log_info(
            "route.added",
            f"Route added: {url} -> {func.__name__}",
            "client_server.add_route",
            func.__name__,
        )

    def render_site(self) -> Tuple[str, str]:
        """
        Renders the initial site HTML. This is called to create the site
        framing structure that includes the frame, header, body, footer, form, and
        debug info.

        :return: The rendered HTML of the initial site.
        """
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
        return site, self.site.title

    def register_monitor_listener(self, handler: Any) -> None:
        """
        Registers a listener to the monitor.

        :param handler: The handler function to register.
        :return: None
        """
        self.monitor.register_listener(handler)
