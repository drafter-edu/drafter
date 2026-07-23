"""
Route signature introspection.

The binder (see :mod:`drafter.router.parameters.binding`) needs richer
signature metadata than just names and types: defaults, parameter kind,
whether a parameter is framework-injected, and aliases. This module turns a
route function into a :class:`RouteSignatureSpec` capturing all of that.
"""

import inspect
from dataclasses import dataclass
from typing import Any, Optional


@dataclass
class RouteParamSpec:
    """A single parameter of a route function.

    Attributes:
        name: The parameter name.
        annotation: The type annotation, or ``inspect.Parameter.empty``.
        has_default: Whether the parameter declares a default value.
        default: The default value (meaningless if ``has_default`` is False).
        kind: The inspect parameter kind (positional, keyword-only, variadic).
        injected: Whether the framework supplies this parameter, determined
            solely by the name starting with `INJECTED_PARAMETER_PREFIX`
            (an underscore); injected parameters are never required from the
            request payload. Note that `state` is matched by a separate
            name/arity rule during binding and is not marked injected.
        aliases: Alternate payload names that may bind to this parameter.
    """

    name: str
    annotation: Any
    has_default: bool
    default: Any
    kind: inspect._ParameterKind
    injected: bool = False
    aliases: tuple[str, ...] = ()

    @property
    def required(self) -> bool:
        if self.injected:
            return False
        if self.is_variadic:
            return False
        return not self.has_default

    @property
    def is_variadic(self) -> bool:
        return self.kind in (
            inspect.Parameter.VAR_POSITIONAL,
            inspect.Parameter.VAR_KEYWORD,
        )

    @property
    def has_annotation(self) -> bool:
        return self.annotation is not inspect.Parameter.empty

    @property
    def show_name(self) -> bool:
        """Whether the argument is rendered as ``name=value`` in call
        representations (keyword-only and var-keyword parameters)."""
        return self.kind in (
            inspect.Parameter.KEYWORD_ONLY,
            inspect.Parameter.VAR_KEYWORD,
        )

    def describe_annotation(self) -> Optional[str]:
        if not self.has_annotation:
            return None
        if hasattr(self.annotation, "__name__"):
            return self.annotation.__name__
        return str(self.annotation)


@dataclass
class RouteSignatureSpec:
    """Full signature metadata for a route function.

    Attributes:
        function_name: Name of the route handler function.
        params: Every parameter, in declaration order (including variadics).
        accepts_var_keyword: Whether the function declares ``**kwargs``.
        accepts_var_positional: Whether the function declares ``*args``.
    """

    function_name: str
    params: tuple[RouteParamSpec, ...]
    accepts_var_keyword: bool
    accepts_var_positional: bool

    @property
    def named_params(self) -> tuple[RouteParamSpec, ...]:
        """Parameters that can be bound by name (excludes variadics)."""
        return tuple(param for param in self.params if not param.is_variadic)

    @property
    def parameter_names(self) -> list[str]:
        return [param.name for param in self.params]

    def get(self, name: str) -> Optional[RouteParamSpec]:
        for param in self.params:
            if param.name == name:
                return param
        return None

    def to_string(self) -> str:
        """Generate a string representation of the function signature.

        Returns:
            str: Signature string in format "func_name(param: Type, ...)".
        """
        parts = []
        for param in self.params:
            type_name = param.describe_annotation()
            if type_name is None:
                parts.append(param.name)
            else:
                parts.append(f"{param.name}: {type_name}")
        return f"{self.function_name}({', '.join(parts)})"


#: Parameters with these names are supplied by the framework, not the request.
INJECTED_PARAMETER_PREFIX = "_"


def get_signature(func) -> RouteSignatureSpec:
    """Extract parameter metadata from a route function's signature.

    Args:
        func: Function to introspect.

    Returns:
        RouteSignatureSpec: Collected signature information.
    """
    signature_parameters = inspect.signature(func).parameters
    params = tuple(
        RouteParamSpec(
            name=parameter.name,
            annotation=parameter.annotation,
            has_default=parameter.default is not inspect.Parameter.empty,
            default=parameter.default,
            kind=parameter.kind,
            injected=parameter.name.startswith(INJECTED_PARAMETER_PREFIX),
        )
        for parameter in signature_parameters.values()
    )
    return RouteSignatureSpec(
        function_name=func.__name__,
        params=params,
        accepts_var_keyword=any(
            parameter.kind is inspect.Parameter.VAR_KEYWORD
            for parameter in signature_parameters.values()
        ),
        accepts_var_positional=any(
            parameter.kind is inspect.Parameter.VAR_POSITIONAL
            for parameter in signature_parameters.values()
        ),
    )
