import inspect
import io
import json
from typing import Union, Callable, Optional, Tuple, List, Dict, Any
from dataclasses import dataclass
from drafter.config.client_server import ClientServerConfiguration
from drafter.data.files import DrafterBinaryFile, DrafterTextFile
from drafter.helpers.dates import try_convert_datetime
from drafter.monitor.audit import log_warning
from drafter.components.utilities.image_support import HAS_PILLOW, PILImage
from drafter.components.geolocation import Location
from drafter.constants import PREVIOUSLY_PRESSED_BUTTON, SUBMIT_BUTTON_KEY
from drafter.history.forms import remap_hidden_form_parameters
from drafter.data.request import Request
from drafter.history.state import SiteState
from drafter.history.utils import safe_repr
from drafter.router.introspect import get_signature, RouteIntrospection


@dataclass
class Router:
    """Map URL paths to route handler functions and prepare request arguments.

    Attributes:
        routes: Dictionary mapping URL strings to callable handlers.
        signatures: Dictionary mapping URL strings to RouteIntrospection data.
    """

    def __init__(self) -> None:
        self.routes = {}
        self.signatures = {}

    def get_route(self, url: str) -> Optional[Callable]:
        """Retrieve the handler function for a given URL.

        Args:
            url: Route URL path to look up.

        Returns:
            Optional[Callable]: Handler function or None if not found.
        """
        return self.routes.get(url)

    def has_route(self, url: str) -> bool:
        """Check whether a route exists for the given URL.

        Args:
            url: Route URL path to check.

        Returns:
            bool: True if route exists, False otherwise.
        """
        return url in self.routes

    def add_route(self, url: str, func: Callable) -> None:
        """Register a route handler for the given URL.

        Args:
            url: Route URL path.
            func: Handler function to call for requests to this URL.

        TODO:
            Handle ignored parameters.
        """
        self.routes[url] = func
        self.signatures[url] = get_signature(func)

    def reset(self) -> None:
        """Reset router state (currently a no-op).

        Does not remove routes or signatures.
        """

    def clear(self) -> None:
        """Remove all registered routes and signatures."""
        self.routes.clear()
        self.signatures.clear()

    def prepare_arguments(
        self,
        request: Request,
        current_state: SiteState,
        configuration: ClientServerConfiguration,
        extra_dependencies: dict[str, Any],
    ) -> tuple[list[Any], dict[str, Any], str]:
        """Prepare positional and keyword arguments for route invocation.

        Orchestrates parameter extraction, remapping, type conversion, and
        validation to construct arguments matching the target function's signature.

        Args:
            request: Incoming client request with form data.
            current_state: Current application state (injected if expected).
            configuration: Server configuration context.

        Returns:
            Tuple of (args list, kwargs dict, representation string).

        Raises:
            ValueError: If parameters are invalid or unconvertible.
        """
        args, kwargs = [], request.kwargs.copy()
        button_pressed = self.preprocess_button_press(kwargs)
        signature = self.get_signature(request)
        kwargs = remap_hidden_form_parameters(kwargs, button_pressed)
        self.flatten_kwargs(kwargs)
        self.inject_state(signature, args, kwargs, current_state)
        self.inject_other_dependencies(signature, args, kwargs, extra_dependencies)
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
        """Generate a string representation of function call arguments.

        Args:
            signature: Introspection data for the target function.
            args: Positional arguments list.
            kwargs: Keyword arguments dictionary.

        Returns:
            str: Function signature string like "func(arg1, kwarg=val2)".
        """
        arguments = ", ".join(
            [safe_repr(arg, escape=False) for arg in args]
            + [
                f"{key}={safe_repr(value, escape=False)}"
                if signature.show_names.get(key, False)
                else safe_repr(value, escape=False)
                for key, value in sorted(
                    kwargs.items(),
                    key=lambda item: signature.expected_parameters.index(item[0]),
                )
            ]
        )
        return f"{signature.function_name}({arguments})"

    def verify_expected_parameters(
        self,
        request: Request,
        signature: RouteIntrospection,
        kwargs: Dict[str, Any],
    ) -> None:
        """Ensure all provided kwargs match the function signature.

        Args:
            request: Associated request for error context.
            signature: Function signature introspection data.
            kwargs: Keyword arguments provided by the request.

        Raises:
            ValueError: If any kwargs don't match expected parameters.

        TODO:
            Enhance to allow default values from function signature.
        """
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
        """Convert a parameter value to its expected type.

        Handles special cases like file uploads, datetime conversions, and
        type-generic containers before attempting standard type conversion.

        Args:
            parameter: Parameter name (for error messages).
            value: Current parameter value.
            expected_types: Dict mapping parameter names to expected types.

        Returns:
            Converted value, or original if no conversion needed.

        Raises:
            ValueError: If conversion fails or is not possible.
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
        success, file_result = self.try_file_upload_conversion(value, expected_type)
        if success:
            return file_result

        # If already correct type, return as-is
        if isinstance(value, expected_type):
            return value

        # Let our custom handlers have a try
        success, potential_conversion = self.try_special_conversion(
            value, expected_type
        )
        if success:
            return potential_conversion

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

    def try_file_upload_conversion(
        self, value: Any, target_type: Any
    ) -> tuple[bool, Any]:
        """Convert file upload metadata to the target type.

        File uploads are received from the client as dicts with keys:
        __file_upload__, filename, content (base64), type, size.

        Args:
            value: File upload dict or other value.
            target_type: Desired type (bytes, str, dict, DrafterBinaryFile, etc).

        Returns:
            Tuple of (success bool, converted value or None).

        Raises:
            ValueError: If file content cannot be decoded or opened (for images).
        """
        # print("Trying file upload conversion.", value, target_type)
        if not isinstance(value, dict) or not value.get("__file_upload__"):
            return False, None

        # Decode the base64 content
        content = value.get("content", b"")
        filename = value.get("filename", "unknown")

        # Convert based on target type
        if target_type is bytes:
            return True, content
        elif target_type is str:
            if not content:
                return True, ""
            try:
                return True, content.decode("utf-8")
            except UnicodeDecodeError as e:
                raise ValueError(
                    f"Could not decode file {filename} as a string of unicode text (utf-8). Perhaps the file is not the type that you expected, or the parameter type is inappropriate?"
                ) from e
        elif target_type is dict:
            return True, {
                "filename": filename,
                "content": content,
                "type": value.get("type"),
                "size": value.get("size"),
            }
        elif target_type is DrafterBinaryFile:
            return True, DrafterBinaryFile(
                filename=filename,
                content=content,
                content_type=value.get("type", "application/octet-stream"),
                size=value.get("size", len(content)),
            )
        elif target_type is DrafterTextFile:
            if not content:
                text_content = ""
            else:
                try:
                    text_content = content.decode("utf-8")
                except UnicodeDecodeError as e:
                    raise ValueError(
                        f"Could not decode file {filename} as a string of unicode text (utf-8). Perhaps the file is not the type that you expected, or the parameter type is inappropriate?"
                    ) from e
            return True, DrafterTextFile(
                filename=filename,
                content=text_content,
                content_type=value.get("type", "text/plain"),
                size=value.get("size", len(text_content)),
            )
        elif HAS_PILLOW and (
            target_type == PILImage.Image
            or (
                inspect.isclass(target_type) and issubclass(target_type, PILImage.Image)
            )
        ):
            if not content:
                return True, None
            try:
                image = PILImage.open(io.BytesIO(content))
                image.filename = filename
                return True, image
            except Exception as e:
                raise ValueError(
                    f"Could not open image file {filename} as a PIL.Image. Perhaps the file is not an image, or the parameter type is inappropriate?"
                ) from e

        # If no special conversion, return the dict
        return False, value

    def try_special_conversion(self, value: Any, target_type: Any) -> tuple[bool, Any]:
        """Attempt special type conversions like datetime parsing and Location data.

        Args:
            value: Current value to convert.
            target_type: Desired target type.

        Returns:
            Tuple of (success bool, converted value or None).
        """
        # Try datetime conversion
        outcome, result = try_convert_datetime(value, target_type)
        if outcome:
            return True, result
        
        # Try Location conversion
        if target_type is Location:
            if isinstance(value, str):
                # Parse JSON string from hidden input
                import json
                try:
                    data = json.loads(value)
                    return True, Location(**data)
                except (json.JSONDecodeError, TypeError) as e:
                    # Return empty location with error status
                    return True, Location(
                        status="error",
                        message=f"Failed to parse location data: {str(e)}"
                    )
            elif isinstance(value, dict):
                # Direct dict, convert to Location
                return True, Location(**value)
            elif isinstance(value, Location):
                # Already a Location object
                return True, value
        
        return False, None

    def convert_argument_types(
        self,
        signature: RouteIntrospection,
        args: List[Any],
        kwargs: Dict[str, Any],
    ) -> Tuple[List[Any], Dict[str, Any]]:
        """Convert all arguments to types expected by the function signature.

        Args:
            signature: Function introspection with expected types.
            args: Positional arguments to convert.
            kwargs: Keyword arguments to convert.

        Returns:
            Tuple of (converted args list, converted kwargs dict).
        """
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
        """Remove excess arguments beyond what the function signature expects.

        Logs a warning if extra arguments are present.

        Args:
            request: Associated request for context/error logging.
            signature: Function signature introspection data.
            args: Positional arguments list (modified in-place).
            kwargs: Keyword arguments dict (modified in-place).

        TODO:
            Allow route functions to suppress unused argument warnings.
        """
        # TODO: Allow the target route function to quiet this warning
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
        """Retrieve function signature metadata for a request URL.

        Args:
            request: Request with URL to look up.

        Returns:
            RouteIntrospection: Signature metadata for the route.

        Raises:
            ValueError: If no signature is registered for the URL.
        """
        signature = self.signatures.get(request.url)
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
        """Inject current state as first argument if function expects it.

        Args:
            signature: Function signature introspection.
            args: Positional arguments list (modified in-place).
            kwargs: Keyword arguments dict.
            current_state: State object to inject.

        TODO:
            Look for state elsewhere in argument list.
        """
        if (
            signature.expected_parameters
            and signature.expected_parameters[0] == "state"
        ) or (len(signature.expected_parameters) - 1 == len(args) + len(kwargs)):
            # TODO: Someone, somewhere needs to copy state, right?
            args.insert(0, current_state)

    def inject_other_dependencies(
        self,
        signature: RouteIntrospection,
        args: list[Any],
        kwargs: dict[str, Any],
        extra_dependencies: dict[str, Any],
    ) -> None:
        """Inject other dependencies like configuration if function expects them.

        Args:
            signature: Function signature introspection.
            args: Positional arguments list (modified in-place).
            kwargs: Keyword arguments dict.
            current_state: State object to extract configuration from.
        """
        for dep_name, dep_value in extra_dependencies.items():
            if dep_name in signature.expected_parameters:
                kwargs[dep_name] = dep_value

    def flatten_kwargs(self, kwargs: Dict[str, Any]) -> None:
        """Unwrap single-element lists in kwargs for cleaner parameter passing.

        Args:
            kwargs: Keyword arguments dict (modified in-place).

        TODO:
            Warn when data is lost in unwrapping.
            Handle other cases appropriately.
        """
        for key, value in kwargs.items():
            if isinstance(value, list) and len(value) == 1:
                # TODO: Warn if this happens and data is being lost?
                kwargs[key] = value[0]
            # TODO: What happens in the other cases?

    def preprocess_button_press(self, kwargs: Dict[str, Any]) -> str:
        """Extract button metadata from form submission data.

        Handles both the current button press and the previously-pressed
        button namespace, extracting and JSON-decoding as needed.

        Args:
            kwargs: Form data dict (modified to remove button keys).

        Returns:
            str: Button namespace/identifier, or empty string if no button.
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
