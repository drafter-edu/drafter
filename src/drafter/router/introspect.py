import inspect
from dataclasses import dataclass
from typing import Any, Dict, List, Tuple


@dataclass
class RouteIntrospection:
    """
    Holds introspection information about a route function.

    :ivar expected_parameters: A list of parameter names that the function expects.
    :ivar show_names: A dictionary mapping parameter names to a boolean indicating
        whether they should be shown as keyword arguments.
    """

    expected_parameters: List[str]
    show_names: Dict[str, bool]
    expected_types: Dict[str, Any]
    function_name: str


def get_signature(func):
    """
    Get the signature of a function.

    :param func: The function to get the signature of.
    :return: The signature of the function.
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
