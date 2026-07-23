"""
Core type-conversion machinery for route parameters.

This module is a light leaf in the data layer: it must not import from the
component or router layers, so that both can import it eagerly. Components
register component-specific converters into :data:`CONVERTER_REGISTRY`
(conventionally imported via ``drafter.components.utilities.registry``);
the router installs the shared cross-component converters when
:mod:`drafter.router.parameters.conversion` loads, since the router owns
conversion policy.

A converter is a function taking a :class:`ConversionContext` and returning:

- ``None`` when it does not apply to the value (the next converter is tried),
- ``ConversionResult(ok=True, value=...)`` on success,
- ``ConversionResult(ok=False, message=..., hint=...)`` on a definitive
  failure, with a student-facing message and fix hint.
"""

import inspect
import types
from dataclasses import dataclass, replace
from typing import Any, Callable, Literal, Optional, Union, get_args, get_origin

from drafter.data.payload import PayloadValue, describe_source


@dataclass
class ConversionContext:
    """Everything a converter needs to convert one parameter value.

    The first block of fields is provided by the caller (the binder); the
    second block is filled in by the ConverterRegistry before converters run.
    """

    param_name: str
    expected_type: Any
    raw_value: Any
    payload_value: Optional[PayloadValue] = None
    route_name: str = ""

    #: The annotation with generics resolved to their origin (List[str] -> list).
    resolved_type: Any = None
    #: Type arguments of a generic annotation (List[str] -> (str,)).
    type_args: tuple = ()
    #: The registry running this conversion, for recursive element conversion.
    registry: Any = None


@dataclass
class ConversionResult:
    ok: bool
    value: Any = None
    error_code: str = ""
    message: str = ""
    hint: str = ""


#: A converter returns None when it does not apply to the given value,
#: letting the next registered converter (or the fallback) try instead.
ConverterFn = Callable[[ConversionContext], Optional[ConversionResult]]


#: Origins that represent a union annotation (typing.Union and PEP 604 `X | Y`).
_UNION_ORIGINS = {Union, getattr(types, "UnionType", Union)}

#: Plain collection types the collection converter handles.
COLLECTION_TYPES = (list, tuple, set, frozenset)


def describe_type(expected_type: Any) -> str:
    """Student-facing name for a type annotation."""
    if expected_type is None or expected_type is type(None):
        return "None"
    if hasattr(expected_type, "__name__"):
        return expected_type.__name__
    return str(expected_type)


def preview_value(value: Any, limit: int = 60) -> str:
    """Short repr of a value, safe to embed in an error message."""
    try:
        text = repr(value)
    except Exception:
        text = f"<{type(value).__name__}>"
    if len(text) > limit:
        text = text[: limit - 3] + "..."
    return text


def conversion_failure(
    ctx: ConversionContext, expected_type: Any, hint: str = ""
) -> ConversionResult:
    """Build the standard student-facing conversion error.

    Example message: ``Parameter 'age' expects int but got 'twenty' from the
    form field 'age'.``
    """
    expected_name = describe_type(expected_type)
    message = (
        f"Parameter '{ctx.param_name}' expects {expected_name} but got "
        f"{preview_value(ctx.raw_value)} from "
        f"{describe_source(ctx.payload_value, ctx.param_name)}."
    )
    return ConversionResult(
        ok=False,
        error_code="conversion_failed",
        message=message,
        hint=hint
        or (
            f"Try providing a valid {expected_name}, or change the "
            f"parameter's type annotation."
        ),
    )


@dataclass
class RegisteredConverter:
    applies_to: Callable[[Any], bool]
    convert: ConverterFn
    priority: int
    name: str


class ConverterRegistry:
    """Priority-ordered chain of converters, dispatched by target type.

    Converters registered with a lower priority number run earlier. All
    converters run *before* the isinstance short-circuit, so a converter can
    intercept values that already look like the target type (e.g. a file
    upload dict for a ``dict`` parameter).
    """

    def __init__(self) -> None:
        self._converters: list[RegisteredConverter] = []

    def register(
        self,
        target_type: Any,
        converter: ConverterFn,
        *,
        priority: int = 100,
        name: str = "",
    ) -> None:
        """Register a converter for one exact target type."""
        self.register_predicate(
            lambda resolved, _target=target_type: resolved is _target,
            converter,
            priority=priority,
            name=name or f"{describe_type(target_type)} converter",
        )

    def register_predicate(
        self,
        applies_to: Callable[[Any], bool],
        converter: ConverterFn,
        *,
        priority: int = 100,
        name: str = "",
    ) -> None:
        """Register a converter for any resolved target type matching a predicate."""
        self._converters.append(
            RegisteredConverter(
                applies_to=applies_to,
                convert=converter,
                priority=priority,
                name=name or getattr(converter, "__name__", "converter"),
            )
        )
        self._converters.sort(key=lambda entry: entry.priority)

    def convert(self, ctx: ConversionContext) -> ConversionResult:
        """Convert ``ctx.raw_value`` to ``ctx.expected_type``.

        Untyped (or ``Any``) parameters pass through unconverted; explicitly
        typed parameters convert strictly and produce a structured error on
        failure.
        """
        ctx.registry = self
        expected = ctx.expected_type
        if expected is inspect.Parameter.empty or expected is Any or expected is None:
            return ConversionResult(ok=True, value=ctx.raw_value)
        return self._convert_to(ctx, expected)

    def _convert_to(self, ctx: ConversionContext, expected: Any) -> ConversionResult:
        origin = get_origin(expected)
        if origin in _UNION_ORIGINS:
            return self._convert_union(ctx, expected)
        if origin is Literal:
            return self._convert_literal(ctx, expected)

        resolved = origin if origin is not None else expected
        value = ctx.raw_value
        # Normalize: a one-item list headed for a scalar parameter unwraps.
        if (
            isinstance(value, list)
            and len(value) == 1
            and resolved not in COLLECTION_TYPES
        ):
            value = value[0]
        working = replace(
            ctx,
            expected_type=expected,
            raw_value=value,
            resolved_type=resolved,
            type_args=get_args(expected),
        )
        working.registry = self

        for entry in self._converters:
            try:
                applicable = entry.applies_to(resolved)
            except Exception:
                applicable = False
            if not applicable:
                continue
            result = entry.convert(working)
            if result is not None:
                return result

        try:
            if isinstance(value, resolved):
                return ConversionResult(ok=True, value=value)
        except TypeError:
            return conversion_failure(
                working,
                expected,
                hint="This type annotation is not supported for automatic conversion.",
            )

        try:
            return ConversionResult(ok=True, value=resolved(value))
        except Exception:
            return conversion_failure(working, resolved)

    def _convert_union(self, ctx: ConversionContext, expected: Any) -> ConversionResult:
        members = get_args(expected)
        if ctx.raw_value is None and type(None) in members:
            return ConversionResult(ok=True, value=None)
        non_none = [member for member in members if member is not type(None)]
        # Values that already satisfy a member pass through untouched.
        for member in non_none:
            try:
                if get_origin(member) is None and isinstance(ctx.raw_value, member):
                    return ConversionResult(ok=True, value=ctx.raw_value)
            except TypeError:
                pass
        first_failure: Optional[ConversionResult] = None
        for member in non_none:
            result = self._convert_to(ctx, member)
            if result.ok:
                return result
            if first_failure is None:
                first_failure = result
        return first_failure or conversion_failure(ctx, expected)

    def _convert_literal(
        self, ctx: ConversionContext, expected: Any
    ) -> ConversionResult:
        allowed = get_args(expected)
        value = ctx.raw_value
        if isinstance(value, list) and len(value) == 1:
            value = value[0]
        if value in allowed:
            return ConversionResult(ok=True, value=value)
        if isinstance(value, str):
            for option in allowed:
                if str(option) == value:
                    return ConversionResult(ok=True, value=option)
        return conversion_failure(
            ctx,
            expected,
            hint="Expected one of: "
            + ", ".join(repr(option) for option in allowed)
            + ".",
        )


#: The shared registry the router uses. Components register component-specific
#: converters into it at import time; the shared cross-component converters
#: are installed by drafter.router.parameters.conversion when the router loads.
CONVERTER_REGISTRY = ConverterRegistry()
