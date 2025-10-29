from dataclasses import dataclass
from typing import Any, List, Tuple
import json
import inspect
import base64
import io

from drafter.history.state import SiteState
from drafter.data.errors import DrafterError
from drafter.payloads.error_page import ErrorPage, SimpleErrorPage
from drafter.payloads.payloads import ResponsePayload
from drafter.data.request import Request
from drafter.data.response import Response
from drafter.data.outcome import Outcome
from drafter.routes import Router
from drafter.audit import AuditLogger
from drafter.config.client_server import ClientServerConfiguration
from drafter.constants import SUBMIT_BUTTON_KEY, PREVIOUSLY_PRESSED_BUTTON
from drafter.history import remap_hidden_form_parameters, safe_repr
from drafter.components.utilities.image_support import HAS_PILLOW, PILImage


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

    def prepare_args(
        self, route_func: Any, request: Request
    ) -> Tuple[List[Any], dict, str]:
        """
        Processes and prepares arguments for the route function call, ensuring compatibility
        with expected parameters, handling state insertion, remapping parameters,
        and performing type conversion when necessary.

        :param route_func: The route function whose parameters are being prepared.
        :param request: The request containing the kwargs to process.
        :return: A tuple containing:
            - Processed positional arguments matching the expected parameters.
            - Processed keyword arguments matching the expected parameters.
            - A string representation of the final arguments for logging.
        """
        args = list(request.args) if request.args else []
        kwargs = dict(request.kwargs) if request.kwargs else {}
        button_pressed = ""

        # Extract button pressed from kwargs
        if SUBMIT_BUTTON_KEY in kwargs:
            button_value = kwargs.pop(SUBMIT_BUTTON_KEY)
            # The value might be a list from FormData, extract first element
            if isinstance(button_value, list) and button_value:
                button_value = button_value[0]
            try:
                button_pressed = json.loads(button_value)
            except (json.JSONDecodeError, TypeError):
                button_pressed = button_value
        elif PREVIOUSLY_PRESSED_BUTTON in kwargs:
            button_value = kwargs.pop(PREVIOUSLY_PRESSED_BUTTON)
            if isinstance(button_value, list) and button_value:
                button_value = button_value[0]
            try:
                button_pressed = json.loads(button_value)
            except (json.JSONDecodeError, TypeError):
                button_pressed = button_value

        # Get function signature
        signature_parameters = inspect.signature(route_func).parameters
        expected_parameters = list(signature_parameters.keys())
        show_names = {
            param.name: (
                param.kind
                in (inspect.Parameter.KEYWORD_ONLY, inspect.Parameter.VAR_KEYWORD)
            )
            for param in signature_parameters.values()
        }

        # Remap hidden form parameters
        kwargs = remap_hidden_form_parameters(kwargs, button_pressed)

        # Convert list values from FormData to single values
        # FormData might wrap values in lists
        for key, value in kwargs.items():
            if isinstance(value, list) and len(value) == 1:
                kwargs[key] = value[0]

        # Insert state into the beginning of args if needed
        if (expected_parameters and expected_parameters[0] == "state") or (
            len(expected_parameters) - 1 == len(args) + len(kwargs)
        ):
            args.insert(0, self.state.current)

        # Check if there are too many arguments
        if len(expected_parameters) < len(args) + len(kwargs):
            self.logger.log_warning(
                f"Too many arguments for {route_func.__name__}",
                "client_server.prepare_args",
                f"Expected {len(expected_parameters)} parameters: {', '.join(expected_parameters)}\n"
                f"But got {len(args) + len(kwargs)}: args={repr(args)}, kwargs={repr(kwargs)}",
            )
            # Trim excess arguments
            args = args[: len(expected_parameters)]
            while len(expected_parameters) < len(args) + len(kwargs) and kwargs:
                kwargs.pop(list(kwargs.keys())[-1])

        # Type conversion if required
        expected_types = {
            name: p.annotation
            for name, p in signature_parameters.items()
        }
        args = [
            self.convert_parameter(param, val, expected_types)
            for param, val in zip(expected_parameters, args)
        ]
        kwargs = {
            param: self.convert_parameter(param, val, expected_types)
            for param, val in kwargs.items()
        }

        # Verify all arguments are in expected_parameters
        for key, value in kwargs.items():
            if key not in expected_parameters:
                self.logger.log_error(
                    f"Unexpected parameter in {route_func.__name__}",
                    "client_server.prepare_args",
                    f"Parameter {key}={value!r} is not in expected parameters: {expected_parameters}",
                )
                raise ValueError(
                    f"Unexpected parameter {key}={value!r} in {route_func.__name__}. "
                    f"Expected parameters: {expected_parameters}"
                )

        # Build representation for logging
        representation = [safe_repr(arg) for arg in args] + [
            f"{key}={safe_repr(value)}"
            if show_names.get(key, False)
            else safe_repr(value)
            for key, value in sorted(
                kwargs.items(), key=lambda item: expected_parameters.index(item[0])
            )
        ]
        return args, kwargs, ", ".join(representation)

    def try_file_upload_conversion(self, value: Any, target_type: Any) -> Any:
        """
        Attempts to convert file upload data to the specified target type.
        File uploads come from the client as dicts with filename, content (base64), type, size.
        
        :param value: The file upload data (dict with __file_upload__ marker).
        :param target_type: The desired type to convert to.
        :return: The converted value.
        """
        if not isinstance(value, dict) or not value.get('__file_upload__'):
            return None
            
        # Decode the base64 content
        content_base64 = value.get('content', '')
        filename = value.get('filename', 'unknown')
        
        try:
            file_bytes = base64.b64decode(content_base64)
        except Exception as e:
            raise ValueError(f"Could not decode file data for {filename}") from e
        
        # Convert based on target type
        if target_type is bytes:
            return file_bytes
        elif target_type is str:
            try:
                return file_bytes.decode("utf-8")
            except UnicodeDecodeError as e:
                raise ValueError(
                    f"Could not decode file {filename} as utf-8. Perhaps the file is not the type that you expected, or the parameter type is inappropriate?"
                ) from e
        elif target_type is dict:
            return {"filename": filename, "content": file_bytes}
        elif HAS_PILLOW and (target_type == PILImage.Image or (inspect.isclass(target_type) and issubclass(target_type, PILImage.Image))):
            try:
                image = PILImage.open(io.BytesIO(file_bytes))
                image.filename = filename
                return image
            except Exception as e:
                raise ValueError(
                    f"Could not open image file {filename} as a PIL.Image. Perhaps the file is not an image, or the parameter type is inappropriate?"
                ) from e
        
        # If no special conversion, return the dict
        return value

    def convert_parameter(self, param: str, val: Any, expected_types: dict) -> Any:
        """
        Converts a parameter value to the expected type if specified.

        :param param: The parameter name.
        :param val: The current value.
        :param expected_types: Dictionary mapping parameter names to expected types.
        :return: The converted value.
        """
        if param not in expected_types:
            return val

        expected_type = expected_types[param]
        if expected_type == inspect.Parameter.empty:
            return val

        # Handle generic types (e.g., List[str])
        if hasattr(expected_type, "__origin__"):
            expected_type = expected_type.__origin__

        # Check if this is a file upload and try file-specific conversions first
        # (before checking if it's already the right type, since file uploads come as dicts)
        file_result = self.try_file_upload_conversion(val, expected_type)
        if file_result is not None:
            return file_result

        # If already correct type, return as-is
        if isinstance(val, expected_type):
            return val

        # Try to convert
        try:
            return expected_type(val)
        except Exception as e:
            try:
                from_name = type(val).__name__
                to_name = expected_types[param].__name__
            except (AttributeError, KeyError):
                from_name = repr(type(val))
                to_name = repr(expected_types[param])
            raise ValueError(
                f"Could not convert {param} ({val!r}) from {from_name} to {to_name}"
            ) from e

    def visit(self, request: Request) -> Any:
        """
        Uses the information in the request to find and call the appropriate route function.

        :param request: The request to process.
        :return: The result of the route function.
        """
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
            return self.make_error_response(request.id, error, status_code=404)
        
        # Prepare arguments for the route function
        try:
            args, kwargs, arguments_repr = self.prepare_args(route_func, request)
            self.logger.log_info(
                f"Prepared arguments for {route_func.__name__}",
                "client_server.visit",
                f"Arguments: {arguments_repr}",
            )
        except Exception as e:
            error = self.logger.log_error(
                f"Error preparing arguments for URL {request.url}: {e}",
                "client_server.visit",
                f"Request: {repr(request)}\nRoute function: {route_func.__name__}",
                request.url,
                e,
            )
            return self.make_error_response(request.id, error)
        
        # Call the route function to get the payload
        try:
            payload = route_func(*args, **kwargs)
        except Exception as e:
            error = self.logger.log_error(
                f"Error while processing request for URL {request.url}: {e}",
                "client_server.visit",
                f"Request: {repr(request)}\nArguments: {arguments_repr}",
                request.url,
                e,
            )
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
        return response

    def report_outcome(self, outcome: Outcome) -> None:
        """
        Reports the outcome of a request processing back to the server.

        :param outcome: The outcome to report.
        :return: None
        """
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
