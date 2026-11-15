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
from collections.abc import Callable
from dataclasses import dataclass, replace
from typing import Any, Literal, Union, get_args, get_origin

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
    payload_value: PayloadValue | None = None
    route_name: str = ""

    #: The annotation with generics resolved to their origin (List[str] -> list).
    resolved_type: Any = None
    #: Type arguments of a generic annotation (List[str] -> (str,)).
    type_args: tuple = ()
    #: The registry running this conversion, for recursive element conversion.
    registry: Any = None


@dataclass
class ConversionResult:
    """The outcome of one conversion attempt.

    Attributes:
        ok: Whether the conversion succeeded.
        value: The converted value, when `ok` is True. For a missing
            value (see `has_empty_value`), the type's own empty value.
        error_code: Stable, code-like identifier for the failure
            (e.g. `conversion_failed`), when `ok` is False.
        message: Student-facing description of the failure.
        hint: Student-facing suggestion for fixing the failure.
        has_empty_value: Only meaningful for a missing-value failure
            (`MISSING_VALUE_ERROR_CODE`). True when the type has a value
            that stands for "nothing was provided", held in `value`: the
            current date for a `date`, the empty string for the text of a
            file that was not chosen. It is used when the parameter is
            neither optional nor given a default.
    """

    ok: bool
    value: Any = None
    error_code: str = ""
    message: str = ""
    hint: str = ""
    has_empty_value: bool = False


ConverterFn = Callable[[ConversionContext], ConversionResult | None]
"""A converter function; it returns None when it does not apply to the given
value, letting the next registered converter (or the fallback) try instead."""

MISSING_VALUE_ERROR_CODE = "missing_value"
"""Failure code for "the value is absent": a number or date field left
blank, a file that was not chosen, a camera that took no photo.

One rule decides what the parameter receives, in this order:

1. None, when the annotation allows it (``int | None``). Union conversion
   does this.
2. The parameter's default, when it has one (``age: int = 7``). The binder
   does this, since defaults belong to the route's signature.
3. The type's own empty value, when it has one (the current date for a
   ``date``, ``""`` for the text of a file that was not chosen).
4. Otherwise the request fails with a message that says no value was
   provided.

Blank text is not absent for ``str`` (it is the empty string) or ``bool``
(an unchecked box), so those never report a missing value for it."""

NO_EMPTY_VALUE: Any = object()
"""Marks a missing value whose type has nothing that stands for "empty"
(there is no empty ``int``)."""


#: Origins that represent a union annotation (typing.Union and PEP 604 `X | Y`).
_UNION_ORIGINS = {Union, getattr(types, "UnionType", Union)}

COLLECTION_TYPES = (list, tuple, set, frozenset)
"""Plain collection types the collection converter handles."""


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


def missing_value_failure(
    ctx: ConversionContext,
    expected_type: Any,
    hint: str = "",
    empty_value: Any = NO_EMPTY_VALUE,
) -> ConversionResult:
    """Build the result for an absent value.

    Used when the client submitted "nothing" for a parameter (a blank
    number field, no file chosen, no photo captured). What the parameter
    then receives follows the rule described at `MISSING_VALUE_ERROR_CODE`;
    the message and hint here are shown only when that rule ends in a
    failure.

    Args:
        ctx: The conversion being attempted.
        expected_type: The type the parameter expects.
        hint: Suggestion for fixing the failure; a general one is used
            when not given.
        empty_value: The type's own stand-in for "nothing was provided",
            when it has one.

    Returns:
        A failed result with the missing-value code.
    """
    expected_name = describe_type(expected_type)
    message = (
        f"Parameter '{ctx.param_name}' expects {expected_name} but no value "
        f"was provided by {describe_source(ctx.payload_value, ctx.param_name)}."
    )
    has_empty_value = empty_value is not NO_EMPTY_VALUE
    return ConversionResult(
        ok=False,
        value=empty_value if has_empty_value else None,
        error_code=MISSING_VALUE_ERROR_CODE,
        message=message,
        hint=hint
        or (
            f"If it is okay for no value to be provided, give the parameter "
            f"a default value or make it optional ({expected_name} | None)."
        ),
        has_empty_value=has_empty_value,
    )


def is_blank_text(value: Any) -> bool:
    """Whether a value is text with nothing in it but spaces.

    Args:
        value: A raw request value.

    Returns:
        True for an empty or all-whitespace string, False for anything
        else (including None and non-text values).
    """
    return isinstance(value, str) and not value.strip()


@dataclass
class RegisteredConverter:
    """One converter entry in a ConverterRegistry.

    Attributes:
        applies_to: Predicate over the resolved target type; the converter
            only runs when this returns True.
        convert: The converter function itself.
        priority: Ordering within the registry; lower numbers run earlier.
        name: Human-readable name for debugging.
    """

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

        def applies_to(resolved: Any, _target=target_type) -> bool:
            return resolved is target_type

        self.register_predicate(
            applies_to,
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

    def convert(
        self, ctx: ConversionContext, keep_missing: bool = False
    ) -> ConversionResult:
        """Convert ``ctx.raw_value`` to ``ctx.expected_type``.

        Untyped (or ``Any``) parameters pass through unconverted; explicitly
        typed parameters convert strictly and produce a structured error on
        failure.

        Args:
            ctx: The conversion to perform.
            keep_missing: How to report a value that is absent (see
                `MISSING_VALUE_ERROR_CODE`) when the annotation does not
                allow None. By default the type's own empty value is
                returned as a success when there is one. The binder
                passes True to get the missing-value failure itself, so
                it can use the parameter's default first.

        Returns:
            The outcome of the conversion.
        """
        ctx.registry = self
        expected = ctx.expected_type
        if expected is inspect.Parameter.empty or expected is Any or expected is None:
            return ConversionResult(ok=True, value=ctx.raw_value)
        result = self._convert_to(ctx, expected)
        if keep_missing or result.ok or not result.has_empty_value:
            return result
        return ConversionResult(ok=True, value=result.value)

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
        first_failure: ConversionResult | None = None
        for member in non_none:
            result = self._convert_to(ctx, member)
            if result.ok:
                return result
            if result.error_code == MISSING_VALUE_ERROR_CODE and type(None) in members:
                # The value is absent and the annotation allows None: an
                # optional parameter simply receives None.
                return ConversionResult(ok=True, value=None)
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
        if is_blank_text(value):
            return missing_value_failure(
                ctx,
                expected,
                hint="Choose one of: "
                + ", ".join(repr(option) for option in allowed)
                + ".",
            )
        return conversion_failure(
            ctx,
            expected,
            hint="Expected one of: "
            + ", ".join(repr(option) for option in allowed)
            + ".",
        )


CONVERTER_REGISTRY = ConverterRegistry()
"""The shared registry the router uses. Components register component-specific
converters into it at import time; the shared cross-component converters
are installed by drafter.router.parameters.conversion when the router loads."""
