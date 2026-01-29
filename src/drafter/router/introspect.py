import inspect
from dataclasses import dataclass
from typing import Any, Dict, List, Tuple


@dataclass
class RouteIntrospection:
    """Store introspection metadata for a route function signature.

    Attributes:
        expected_parameters: List of parameter names the function accepts.
        show_names: Dict mapping parameter names to whether shown as kwargs.
        expected_types: Dict mapping parameter names to their type hints.
        function_name: Name of the route handler function.
    """

    expected_parameters: list[str]
    show_names: dict[str, bool]
    expected_types: dict[str, Any]
    function_name: str

    def to_string(self) -> str:
        """Generate a string representation of the function signature.

        Returns:
            str: Signature string in format "func_name(param: Type, ...)".
        """
        parts = []
        for param in self.expected_parameters:
            expected_type = self.expected_types.get(param, Any)
            type_name = (
                expected_type.__name__
                if hasattr(expected_type, "__name__")
                else (
                    str(expected_type)
                    if expected_type is not inspect.Parameter.empty
                    else None
                )
            )
            if type_name is None:
                parts.append(f"{param}")
            else:
                parts.append(f"{param}: {type_name}")
        params_str = ", ".join(parts)
        return f"{self.function_name}({params_str})"


def get_signature(func):
    """Extract parameter metadata from a function signature.

    Inspects the function using the inspect module to determine which
    parameters it accepts, their names, types, and kinds.

    Args:
        func: Function to introspect.

    Returns:
        RouteIntrospection: Collected signature information.
    """
    # Get function signature
    signature_parameters = inspect.signature(func).parameters
    expected_parameters = list(signature_parameters.keys())
    show_names = {
        param.name: (
            param.kind
            in (inspect.Parameter.KEYWORD_ONLY, inspect.Parameter.VAR_KEYWORD)
        )
        for param in signature_parameters.values()
    }
    expected_types = {name: p.annotation for name, p in signature_parameters.items()}

    return RouteIntrospection(
        expected_parameters=expected_parameters,
        show_names=show_names,
        expected_types=expected_types,
        function_name=func.__name__,
    )
