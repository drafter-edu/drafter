"""
Route signature introspection.

The binder (see :mod:`drafter.router.parameters.binding`) needs richer
signature metadata than just names and types: defaults, parameter kind,
whether a parameter is framework-injected, and aliases. This module turns a
route function into a :class:`RouteSignatureSpec` capturing all of that.
"""

import inspect
from dataclasses import dataclass
from typing import Any


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
        """Whether the request must supply this parameter.

        Injected and variadic parameters are never required; otherwise a
        parameter is required exactly when it has no default value.
        """
        if self.injected:
            return False
        if self.is_variadic:
            return False
        return not self.has_default

    @property
    def is_variadic(self) -> bool:
        """Whether this parameter is ``*args`` or ``**kwargs``."""
        return self.kind in (
            inspect.Parameter.VAR_POSITIONAL,
            inspect.Parameter.VAR_KEYWORD,
        )

    @property
    def has_annotation(self) -> bool:
        """Whether this parameter declares a type annotation."""
        return self.annotation is not inspect.Parameter.empty

    @property
    def show_name(self) -> bool:
        """Whether the argument is rendered as ``name=value`` in call
        representations (keyword-only and var-keyword parameters)."""
        return self.kind in (
            inspect.Parameter.KEYWORD_ONLY,
            inspect.Parameter.VAR_KEYWORD,
        )

    def describe_annotation(self) -> str | None:
        """Render the annotation as a short display name.

        Returns:
            The annotation's ``__name__`` (falling back to ``str()``), or
            None if the parameter has no annotation.
        """
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
        """Names of all parameters, in declaration order."""
        return [param.name for param in self.params]

    def get(self, name: str) -> RouteParamSpec | None:
        """Look up a parameter spec by name.

        Args:
            name: Parameter name to find.

        Returns:
            The matching RouteParamSpec, or None if no parameter has
            that name.
        """
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

    def describe_request_parameters(self) -> list[dict]:
        """Describe the parameters a request can supply, as plain data.

        Skips `state`, framework-injected parameters, and variadics; the
        result is JSON-serializable and shipped to the debug panel so the
        routes list can build parameter forms.

        Returns:
            A list of dicts with "name", "type" (display name or ""),
            "required", and "default" (repr string, or None when the
            parameter has no default).
        """
        parameters = []
        for param in self.params:
            if param.injected or param.is_variadic or param.name == "state":
                continue
            parameters.append(
                {
                    "name": param.name,
                    "type": param.describe_annotation() or "",
                    "required": param.required,
                    "default": repr(param.default) if param.has_default else None,
                }
            )
        return parameters


INJECTED_PARAMETER_PREFIX = "_"
"""Parameters whose names start with this prefix are marked as injected:
supplied by the framework rather than required from the request payload."""


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
