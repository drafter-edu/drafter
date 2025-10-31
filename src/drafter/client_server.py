import html
import os
import traceback
from dataclasses import dataclass, asdict, replace, field, fields
from functools import wraps
from typing import Any, Optional, List, Tuple, Union, Dict
import json
import inspect
import pathlib

from drafter.history.state import SiteState
from drafter.data.errors import DrafterError
from drafter.payloads import Page
from drafter.payloads.error_page import ErrorPage, SimpleErrorPage
from drafter.payloads.payloads import ResponsePayload
from drafter.data.request import Request
from drafter.data.response import Response
from drafter.data.outcome import Outcome
from drafter.routes import Router
from drafter.audit import AuditLogger
from drafter.config.client_server import ClientServerConfiguration
from drafter.monitor import Monitor


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
    :ivar monitor: A Monitor instance for tracking telemetry and generating debug information.
    """

    custom_name: str
    state: SiteState
    configuration: ClientServerConfiguration
    response_count: int = 0

    def __init__(self, custom_name: str) -> None:
        self.router = Router()
        self.state = SiteState()
        self.logger = AuditLogger()
        self.configuration = ClientServerConfiguration()
        self.monitor = Monitor()

    def start(self, initial_state: Any = None) -> None:
        """
        Starts the server with the given initial state.

        :param initial_state: The initial state to set for the server.
        """
        if initial_state is not None:
            self.logger.log_info(
                "Initializing server state",
                "client_server.start",
                f"Initial state: {repr(initial_state)}",
            )
            self.state.update(initial_state)

    def visit(self, request: Request) -> Any:
        """
        Uses the information in the request to find and call the appropriate route function.

        :param request: The request to process.
        :return: The result of the route function.
        """
        # Track the request in the monitor
        self.monitor.track_request(request)
        
        self.logger.log_info(
            f"Request received: {request}",
            "client_server.visit",
            repr(request),
            request.url,
        )
        # Get the route function
        route_func = self.router.get_route(request.url)
        if route_func is None:
            error = self.logger.log_error(
                f"No route found for URL: {request.url}",
                "client_server.visit",
                repr(request),
                request.url,
            )
            self.monitor.track_error(error)
            return self.make_error_response(request.id, error, status_code=404)
        # Call the route function to get the payload
        try:
            payload = route_func(self.state, *request.args, **request.kwargs)
        except Exception as e:
            error = self.logger.log_error(
                f"Error while processing request for URL {request.url}: {e}",
                "client_server.visit",
                repr(request),
                request.url,
                e,
            )
            self.monitor.track_error(error)
            return self.make_error_response(request.id, error)
        # Verify the payload
        if not isinstance(payload, ResponsePayload):
            page_type_name = type(payload).__name__
            error = self.logger.log_error(
                f"Route function for URL {request.url} did not return a Page. Instead got: {page_type_name}",
                "client_server.visit",
                f"Request: {repr(request)}\nPage: {repr(payload)}",
                request.url,
            )
            self.monitor.track_error(error)
            return self.make_error_response(request.id, error)
        # Render the payload
        try:
            body = self.render(payload)
        except Exception as e:
            error = self.logger.log_error(
                f"Error while rendering payload for URL {request.url}: {e}",
                "client_server.visit",
                f"Request: {repr(request)}\nPayload: {repr(payload)}",
                request.url,
                e,
            )
            self.monitor.track_error(error)
            return self.make_error_response(request.id, error)
        # Return successfully
        return self.make_success_response(request.id, body, payload)

    def render(self, payload: ResponsePayload) -> str:
        """
        Renders the given payload to HTML.

        :param payload: The payload to render.
        :return: The rendered HTML as a string.
        """
        return payload.render(self.state, self.configuration)

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
        
        # Track the response with the monitor
        self.monitor.track_response(response, state_snapshot=self.state.current)
        
        # Add debug information to the response via a channel
        if self.configuration.debug_enabled:
            debug_html = self.monitor.generate_debug_html(
                current_state=self.state.current,
                initial_state=self.state.initial,
                routes=self.router.routes,
                server_config=self._get_config_dict(),
            )
            if debug_html:
                response.send("debug", debug_html, kind="html")
        
        return response

    def make_error_response(
        self, request_id: int, error: DrafterError, status_code: int = 500
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
            error_page_error = self.logger.log_error(
                "Failed to create ErrorPage payload",
                "client_server.make_error_response",
                f"Original error: {repr(error)}\nError during ErrorPage creation: {repr(e)}",
                error.url,
                e,
            )
            simpler_error_payload = SimpleErrorPage(error_page_error.message)
            return Response(
                id=self.response_count,
                request_id=request_id,
                payload=simpler_error_payload,
                status_code=500,
                body=simpler_error_payload.render(self.state, self.configuration),
                message=error_page_error.message,
                errors=[error, error_page_error],
            )
        response = Response(
            id=self.response_count,
            request_id=request_id,
            body=body,
            payload=error_payload,
            status_code=status_code,
            message=error.message,
            errors=[error],
        )
        self.response_count += 1
        
        # Track the error response with the monitor
        self.monitor.track_response(response, state_snapshot=self.state.current)
        
        # Add debug information even for error responses
        if self.configuration.debug_enabled:
            debug_html = self.monitor.generate_debug_html(
                current_state=self.state.current,
                initial_state=self.state.initial,
                routes=self.router.routes,
                server_config=self._get_config_dict(),
            )
            if debug_html:
                response.send("debug", debug_html, kind="html")
        
        return response

    def report_outcome(self, outcome: Outcome) -> None:
        """
        Reports the outcome of a request processing back to the server.

        :param outcome: The outcome to report.
        :return: None
        """
        # Track the outcome with the monitor
        self.monitor.track_outcome(outcome)
        
        for error in outcome.errors:
            self.logger.log_existing_error(error)
        for warning in outcome.warnings:
            self.logger.log_existing_warning(warning)
        for info in outcome.info:
            self.logger.log_existing_info(info)
        self.logger.log_info(
            f"Outcome reported: {outcome}",
            "client_server.report_outcome",
            repr(outcome),
        )

    def add_route(self, url: str, func: Any) -> None:
        """
        Adds a new route to the server.

        TODO: Inspect that the route has a valid route signature.

        :param url: The URL to add the route to.
        :param func: The function to call when the route is accessed.
        """
        self.router.add_route(url, func)
        self.logger.log_info(
            f"Route added: {url} -> {func.__name__}",
            "client_server.add_route",
            f"Function: {repr(func)}",
        )
    
    def _get_config_dict(self) -> Dict[str, Any]:
        """
        Get the configuration as a dictionary for the monitor.
        
        :return: Dictionary representation of the configuration
        """
        return {
            "in_debug_mode": self.configuration.in_debug_mode,
            "enable_audit_logging": self.configuration.enable_audit_logging,
            "site_title": self.configuration.site_title,
            "debug_enabled": self.configuration.debug_enabled,
            "custom_name": self.custom_name,
        }


MAIN_SERVER = ClientServer(custom_name="MAIN_SERVER")


def set_main_server(server: ClientServer):
    """
    Sets the main server to the given server. This is useful for testing purposes.

    :param server: The server to set as the main server
    :return: None
    """
    global MAIN_SERVER
    MAIN_SERVER = server


def get_main_server() -> ClientServer:
    """
    Gets the main server. This is useful for testing purposes.

    :return: The main server
    """
    return MAIN_SERVER
