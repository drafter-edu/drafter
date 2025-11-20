from dataclasses import dataclass
from typing import Any, Optional, List, Tuple, Union, Dict
import time

from drafter.client_server.context import Scope
from drafter.client_server.errors import VisitError
from drafter.data.channel import Message
from drafter.history.state import SiteState
from drafter.monitor.events.errors import DrafterError
from drafter.monitor.bus import EventBus
from drafter.monitor.events.request import (
    RequestEvent,
    RequestParseEvent,
    ResponseEvent,
)
from drafter.monitor.events.routes import RouteAddedEvent
from drafter.monitor.events.state import UpdatedStateEvent
from drafter.monitor.monitor import Monitor
from drafter.payloads import Page
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

    def reset(self) -> None:
        """
        Resets the server to its initial state.
        """
        self.state.reset()
        self.router.reset()
        self.site.reset()
        self.monitor.reset()
        self.response_count = 0
        self.requests.reset()

    def process_configuration(self):
        self.site.title = self.configuration.site_title
        self.site.additional_css = self.configuration.additional_css_content
        self.site.additional_style = self.configuration.additional_style_content
        self.site.additional_header = self.configuration.additional_header_content
        self.site.in_debug_mode = self.configuration.in_debug_mode

    def change_debug_mode(self):
        """
        Toggles the debug mode of the website.
        """
        self.configuration.in_debug_mode = not self.configuration.in_debug_mode
        log_info(
            "site.debug_mode_changed",
            "Toggled debug mode",
            "client_server.change_debug_mode",
            f"New debug mode: {self.configuration.in_debug_mode}",
        )

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
            payload.verify(self.router, self.state, self.configuration, request)
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
        self, request: Request, payload: ResponsePayload
    ) -> Optional[str]:
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
                503,
            )

    def format_payload(self, request: Request, payload: ResponsePayload) -> str:
        # Format the payload for display in the history panel
        try:
            return payload.format(self.state, self.configuration)
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

    def handle_state_updates(self, request: Request, payload: ResponsePayload) -> None:
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

    def visit(self, request: Request) -> Any:
        """
        Uses the information in the request to find and call the appropriate route function.

        :param request: The request to process.
        :return: The result of the route function.
        """
        start_time = time.time()
        log_data(
            RequestEvent.from_request(request),
            "client_server.visit",
            route=request.url,
            request_id=request.id,
        )
        with self.requests.push(request):
            try:
                route_func = self.get_route(request)
                payload = self.execute_route(route_func, request)
                self.verify_payload(request, payload)
                body = self.render_payload(request, payload)
                formatted_body = self.format_payload(request, payload)
                self.handle_state_updates(request, payload)
                messages = self.get_messages(request, payload)
            except VisitError as ve:
                return self.make_error_response(
                    request, ve.error, status_code=ve.status_code
                )

        # Return successfully
        try:
            response = self.make_success_response(
                request.id, request.url, body, payload, messages
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
        end_time = time.time()
        response_time = (end_time - start_time) * 1000  # in milliseconds
        log_data(
            ResponseEvent.from_response(response, formatted_body, response_time),
            "client_server.visit",
            route=request.url,
            request_id=request.id,
            response_id=response.id,
        )
        return response

    def make_success_response(
        self,
        request_id: int,
        url: str,
        body: Optional[str],
        payload: ResponsePayload,
        messages: List[Message],
    ) -> Response:
        """
        Makes a successful response for the server with the given page.

        :param request_id: The ID of the request.
        :param body: The rendered body content.
        :param payload: The payload to include in the response.
        :param messages: A list of messages to include in the response.
        :return: The response from the server.
        """
        response = Response(
            id=self.response_count,
            request_id=request_id,
            payload=payload,
            body=body,
            url=url,
        )
        response.send_messages(messages)
        self.response_count += 1

        return response

    def get_messages(self, request: Request, payload: ResponsePayload) -> list[Message]:
        try:
            messages = payload.get_messages(self.state, self.configuration)
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
                url=request.url,
                status_code=500,
                body=simpler_error_payload.render(self.state, self.configuration),
                message=error_page_error.message,
                errors=[error, error_page_error],
            )
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
        log_data(
            RouteAddedEvent(url=url, signature=self.router.signatures[url].to_string()),
            "client_server.add_route",
        )

    def render_site(self) -> InitialSiteData:
        """
        Renders the initial site HTML. This is called to create the site
        framing structure that includes the frame, header, body, footer, form, and
        debug info.

        :return: The rendered HTML of the initial site.
        """
        try:
            self.process_configuration()
        except Exception as e:
            error = log_error(
                "site.processing_failed",
                "Failed to process site configuration",
                "client_server.render_site",
                f"Original exception: {e}",
                exception=e,
            )
            site = f"<div><h1>Error processing site configuration</h1><p>{error.message}</p></div>"
            return InitialSiteData(site_html=site, site_title="Error", error=True)
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

    def register_monitor_listener(self, handler: Any) -> None:
        """
        Registers a listener to the monitor.

        :param handler: The handler function to register.
        :return: None
        """
        self.monitor.register_listener(handler)
