import base64
import inspect
import io
import json
from typing import Union, Callable, Optional, Tuple, List, Dict, Any
from dataclasses import dataclass
from drafter.audit import log_error, log_warning
from drafter.client_server.errors import VisitError
from drafter.components.utilities.image_support import HAS_PILLOW, PILImage
from drafter.constants import PREVIOUSLY_PRESSED_BUTTON, SUBMIT_BUTTON_KEY
from drafter.data.errors import DrafterError
from drafter.history.forms import remap_hidden_form_parameters
from drafter.data.request import Request
from drafter.history.state import SiteState
from drafter.history.utils import safe_repr
from drafter.router.introspect import get_signature, RouteIntrospection


@dataclass
class Router:
    """
    Handles routing of URLs to functions within a server.

    :ivar routes: A dictionary mapping URLs to their corresponding functions.
    :ivar signatures: A dictionary mapping functions to their introspection data.
    """

    def __init__(self) -> None:
        self.routes = {}
        self.signatures = {}

    def get_route(self, url: str) -> Optional[Callable]:
        """
        Retrieves the function associated with a given URL.

        :param url: The URL to look up.
        :return: The function associated with the URL, or None if not found.
        """
        return self.routes.get(url)

    def add_route(self, url: str, func: Callable) -> None:
        """
        Adds a new route to the server.

        :param url: The URL to add the route to.
        :param func: The function to call when the route is accessed.
        """
        self.routes[url] = func

    def prepare_arguments(
        self,
        request: Request,
        current_state: SiteState,
    ) -> Tuple[List[Any], Dict[str, Any], str]:
        """
        Prepares the arguments and keyword arguments for the route function based on the request.

        :param request: The incoming request object.
        :return: A tuple containing a list of positional arguments, a dictionary of keyword arguments, and a string representation of the arguments.
        """
        args, kwargs = request.args.copy(), request.kwargs.copy()
        button_pressed = self.preprocess_button_press(kwargs)
        signature = self.get_signature(request)
        print(button_pressed, kwargs)
        kwargs = remap_hidden_form_parameters(kwargs, button_pressed)
        self.flatten_kwargs(kwargs)
        self.inject_state(signature, args, kwargs, current_state)
        self.trim_excess_arguments(request, signature, args, kwargs)
        args, kwargs = self.convert_argument_types(signature, args, kwargs)
        self.verify_expected_parameters(request, signature, kwargs)
        representation = self.build_argument_representation(signature, args, kwargs)
        return args, kwargs, representation

    def build_argument_representation(
        self,
        signature: RouteIntrospection,
        args: List[Any],
        kwargs: Dict[str, Any],
    ) -> str:
        return ", ".join(
            [safe_repr(arg) for arg in args]
            + [
                f"{key}={safe_repr(value)}"
                if signature.show_names.get(key, False)
                else safe_repr(value)
                for key, value in sorted(
                    kwargs.items(),
                    key=lambda item: signature.expected_parameters.index(item[0]),
                )
            ]
        )

    def verify_expected_parameters(
        self,
        request: Request,
        signature: RouteIntrospection,
        kwargs: Dict[str, Any],
    ) -> None:
        # Verify all arguments are in expected_parameters
        for key, value in kwargs.items():
            if key not in signature.expected_parameters:
                raise ValueError(
                    f"Unexpected parameter {key}={value!r} in {signature.function_name}. "
                    f"Expected parameters: {signature.expected_parameters}"
                )

    def convert_parameter(
        self,
        parameter: str,
        value: Any,
        expected_types: Dict[str, Any],
    ) -> Any:
        """
        Converts a parameter value to the expected type if specified.

        :param param: The parameter name.
        :param val: The current value.
        :param expected_types: Dictionary mapping parameter names to expected types.
        :return: The converted value.
        """
        if parameter not in expected_types:
            return value

        expected_type = expected_types[parameter]
        if expected_type == inspect.Parameter.empty:
            return value

        # Handle generic types (e.g., List[str])
        if hasattr(expected_type, "__origin__"):
            expected_type = expected_type.__origin__

        # Check if this is a file upload and try file-specific conversions first
        # (before checking if it's already the right type, since file uploads come as dicts)
        file_result = self.try_file_upload_conversion(value, expected_type)
        if file_result is not None:
            return file_result

        # If already correct type, return as-is
        if isinstance(value, expected_type):
            return value

        # Try to convert
        try:
            return expected_type(value)
        except Exception as e:
            try:
                from_name = type(value).__name__
                to_name = expected_types[parameter].__name__
            except (AttributeError, KeyError):
                from_name = repr(type(value))
                to_name = repr(expected_types[parameter])
            raise ValueError(
                f"Could not convert {parameter} ({value!r}) from {from_name} to {to_name}"
            ) from e

    def try_file_upload_conversion(self, value: Any, target_type: Any) -> Any:
        """
        Attempts to convert file upload data to the specified target type.
        File uploads come from the client as dicts with filename, content (base64), type, size.

        :param value: The file upload data (dict with __file_upload__ marker).
        :param target_type: The desired type to convert to.
        :return: The converted value.
        """
        print("Trying file upload conversion.", value, target_type)
        if not isinstance(value, dict) or not value.get("__file_upload__"):
            return None

        # Decode the base64 content
        content_base64 = value.get("content", "")
        filename = value.get("filename", "unknown")

        print(value, filename, target_type)

        file_bytes = content_base64
        # try:
        #     file_bytes = base64.b64decode(content_base64)
        # except Exception as e:
        #     raise ValueError(f"Could not decode file data for {filename}") from e

        # Convert based on target type
        if target_type is bytes:
            return file_bytes
        elif target_type is str:
            try:
                return file_bytes  # .decode("utf-8")
            except UnicodeDecodeError as e:
                raise ValueError(
                    f"Could not decode file {filename} as utf-8. Perhaps the file is not the type that you expected, or the parameter type is inappropriate?"
                ) from e
        elif target_type is dict:
            return {
                "filename": filename,
                "content": file_bytes,
                "type": value.get("type"),
                "size": value.get("size"),
            }
        elif HAS_PILLOW and (
            target_type == PILImage.Image
            or (
                inspect.isclass(target_type) and issubclass(target_type, PILImage.Image)
            )
        ):
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

    def convert_argument_types(
        self,
        signature: RouteIntrospection,
        args: List[Any],
        kwargs: Dict[str, Any],
    ) -> Tuple[List[Any], Dict[str, Any]]:
        """Converts argument types based on the expected types in the function signature."""
        args = [
            self.convert_parameter(param, val, signature.expected_types)
            for param, val in zip(signature.expected_parameters, args)
        ]
        kwargs = {
            param: self.convert_parameter(param, val, signature.expected_types)
            for param, val in kwargs.items()
        }
        return args, kwargs

    def trim_excess_arguments(
        self,
        request: Request,
        signature: RouteIntrospection,
        args: List[Any],
        kwargs: Dict[str, Any],
    ) -> None:
        """Trims excess arguments from the args and kwargs lists based on the function signature."""
        # Check if there are too many arguments
        if len(signature.expected_parameters) < len(args) + len(kwargs):
            log_warning(
                "request.unused_arguments",
                f"Too many arguments for {signature.function_name}",
                "router.trim_excess_arguments",
                f"Expected {len(signature.expected_parameters)} parameters: {', '.join(signature.expected_parameters)}\n"
                f"But got {len(args) + len(kwargs)}: args={repr(args)}, kwargs={repr(kwargs)}",
                route=request.url,
            )
            # Trim excess arguments
            args = args[: len(signature.expected_parameters)]
            while (
                len(signature.expected_parameters) < len(args) + len(kwargs) and kwargs
            ):
                kwargs.pop(list(kwargs.keys())[-1])

    def get_signature(self, request: Request) -> RouteIntrospection:
        """
        Retrieves the introspection data associated with a given function.

        :param func: The function to look up.
        :return: The introspection data associated with the function, or None if not found.
        """
        route_func = self.get_route(request.url)
        signature = get_signature(route_func)
        if not signature:
            raise ValueError(f"No signature found for route '{request.url}'")
        return signature

    def inject_state(
        self,
        signature: RouteIntrospection,
        args: List[Any],
        kwargs: Dict[str, Any],
        current_state: SiteState,
    ) -> None:
        if (
            signature.expected_parameters
            and signature.expected_parameters[0] == "state"
        ) or (len(signature.expected_parameters) - 1 == len(args) + len(kwargs)):
            args.insert(0, current_state)

    def flatten_kwargs(self, kwargs: Dict[str, Any]) -> None:
        for key, value in kwargs.items():
            if isinstance(value, list) and len(value) == 1:
                # TODO: Warn if this happens and data is being lost?
                kwargs[key] = value[0]
            # TODO: What happens in the other cases?

    def preprocess_button_press(self, kwargs: Dict[str, Any]) -> str:
        """
        Preprocesses button press information from the request kwargs.

        :param kwargs: The keyword arguments from the request.
        :return: The button namespace if present, otherwise an empty string.
        """
        button_pressed = ""
        if SUBMIT_BUTTON_KEY in kwargs:
            button_value = kwargs.pop(SUBMIT_BUTTON_KEY)
            # The value might be a list from FormData, extract first element
            if isinstance(button_value, list) and button_value:
                button_value = button_value[0]
            try:
                button_pressed = json.loads(button_value)  # type: ignore
            except (json.JSONDecodeError, TypeError):
                button_pressed = button_value
        elif PREVIOUSLY_PRESSED_BUTTON in kwargs:
            button_value = kwargs.pop(PREVIOUSLY_PRESSED_BUTTON)
            if isinstance(button_value, list) and button_value:
                button_value = button_value[0]
            try:
                button_pressed = json.loads(button_value)  # type: ignore
            except (json.JSONDecodeError, TypeError):
                button_pressed = button_value

        return button_pressed  # type: ignore
