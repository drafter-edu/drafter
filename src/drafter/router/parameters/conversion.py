"""
Central type conversion for route parameters.

The router owns conversion policy: strict conversion for explicitly typed
parameters, permissive passthrough for untyped ones. Components contribute
component-specific converters by registering into :data:`CONVERTER_REGISTRY`
(conventionally imported via ``drafter.components.utilities.registry``);
cross-component types (files, datetime, Location, images, dataclasses) are
first-class shared converters registered in this module.

A converter is a function taking a :class:`ConversionContext` and returning:

- ``None`` when it does not apply to the value (the next converter is tried),
- ``ConversionResult(ok=True, value=...)`` on success,
- ``ConversionResult(ok=False, message=..., hint=...)`` on a definitive
  failure, with a student-facing message and fix hint.
"""

import dataclasses
import inspect
import json
import types
from dataclasses import dataclass, replace
from datetime import datetime, date, time
from typing import (
    Any,
    Callable,
    Literal,
    Optional,
    Union,
    get_args,
    get_origin,
    get_type_hints,
)

from drafter.data.converter import ConversionContext, ConversionResult, ConverterFn
from drafter.data.files import DrafterBinaryFile, DrafterTextFile
from drafter.data.payload import describe_source
from drafter.helpers.dates import try_convert_datetime


#: Origins that represent a union annotation (typing.Union and PEP 604 `X | Y`).
_UNION_ORIGINS = {Union, getattr(types, "UnionType", Union)}

#: Plain collection types the collection converter handles.
_COLLECTION_TYPES = (list, tuple, set, frozenset)


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
            and resolved not in _COLLECTION_TYPES
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
            hint="Expected one of: " + ", ".join(repr(option) for option in allowed) + ".",
        )


# --- Shared converters -------------------------------------------------------
# Cross-component types are first-class here so no component duplicates them.


def _accepts_file_upload(target: Any) -> bool:
    try:
        if target in (bytes, str, dict, DrafterBinaryFile, DrafterTextFile):
            return True
    except TypeError:
        return False
    try:
        from drafter.components.utilities.image_support import HAS_PILLOW, PILImage
    except ImportError:
        return False
    return (
        HAS_PILLOW
        and inspect.isclass(target)
        and issubclass(target, PILImage.Image)
    )


def convert_file_upload(ctx: ConversionContext) -> Optional[ConversionResult]:
    """Convert a client file-upload dict (``__file_upload__``) to the target type."""
    value = ctx.raw_value
    if not isinstance(value, dict) or not value.get("__file_upload__"):
        return None

    target = ctx.resolved_type
    content = value.get("content", b"")
    filename = value.get("filename", "unknown")
    text_hint = (
        f"The file {filename!r} does not look like unicode (utf-8) text. "
        f"Perhaps the file is not the type you expected, or the parameter "
        f"type should be bytes instead?"
    )

    if target is bytes:
        return ConversionResult(ok=True, value=content)
    if target is str:
        if not content:
            return ConversionResult(ok=True, value="")
        try:
            return ConversionResult(ok=True, value=content.decode("utf-8"))
        except UnicodeDecodeError:
            return conversion_failure(ctx, str, hint=text_hint)
    if target is dict:
        return ConversionResult(
            ok=True,
            value={
                "filename": filename,
                "content": content,
                "type": value.get("type"),
                "size": value.get("size"),
            },
        )
    if target is DrafterBinaryFile:
        return ConversionResult(
            ok=True,
            value=DrafterBinaryFile(
                filename=filename,
                content=content,
                content_type=value.get("type", "application/octet-stream"),
                size=value.get("size", len(content)),
            ),
        )
    if target is DrafterTextFile:
        if not content:
            text_content = ""
        else:
            try:
                text_content = content.decode("utf-8")
            except UnicodeDecodeError:
                return conversion_failure(ctx, DrafterTextFile, hint=text_hint)
        return ConversionResult(
            ok=True,
            value=DrafterTextFile(
                filename=filename,
                content=text_content,
                content_type=value.get("type", "text/plain"),
                size=value.get("size", len(text_content)),
            ),
        )

    from drafter.components.utilities.image_support import HAS_PILLOW, PILImage
    import io

    if HAS_PILLOW and inspect.isclass(target) and issubclass(target, PILImage.Image):
        if not content:
            return ConversionResult(ok=True, value=None)
        try:
            image = PILImage.open(io.BytesIO(content))
            image.filename = filename
            return ConversionResult(ok=True, value=image)
        except Exception:
            return conversion_failure(
                ctx,
                target,
                hint=(
                    f"Could not open {filename!r} as an image. Perhaps the "
                    f"file is not an image, or the parameter type is "
                    f"inappropriate?"
                ),
            )
    return None


def convert_datetime_like(ctx: ConversionContext) -> Optional[ConversionResult]:
    try:
        outcome, converted = try_convert_datetime(ctx.raw_value, ctx.resolved_type)
    except ValueError:
        return conversion_failure(
            ctx,
            ctx.resolved_type,
            hint=(
                "Use an ISO format like '2024-01-31' or '13:30:00', "
                "e.g. from a date or time input field."
            ),
        )
    if outcome:
        return ConversionResult(ok=True, value=converted)
    return None


def _is_location_type(target: Any) -> bool:
    try:
        from drafter.components.geolocation import Location
    except ImportError:
        return False
    return target is Location


def convert_location(ctx: ConversionContext) -> Optional[ConversionResult]:
    from drafter.components.geolocation import Location

    value = ctx.raw_value
    if isinstance(value, Location):
        return ConversionResult(ok=True, value=value)
    if isinstance(value, str):
        try:
            value = json.loads(value)
        except json.JSONDecodeError as error:
            # An unparseable location is a status, not a crash: routes can
            # inspect the error without students needing try/except.
            return ConversionResult(
                ok=True,
                value=Location(
                    status="error",
                    message=f"Failed to parse location data: {error}",
                ),
            )
    if isinstance(value, dict):
        try:
            return ConversionResult(ok=True, value=Location(**value))
        except TypeError as error:
            return ConversionResult(
                ok=True,
                value=Location(
                    status="error",
                    message=f"Failed to parse location data: {error}",
                ),
            )
    return None


def _is_dataclass_type(target: Any) -> bool:
    return isinstance(target, type) and dataclasses.is_dataclass(target)


def convert_dataclass(ctx: ConversionContext) -> Optional[ConversionResult]:
    """Build a dataclass from a dict (or JSON string), converting each field."""
    target = ctx.resolved_type
    value = ctx.raw_value
    if isinstance(value, target):
        return ConversionResult(ok=True, value=value)
    if isinstance(value, str):
        try:
            value = json.loads(value)
        except json.JSONDecodeError:
            return conversion_failure(
                ctx,
                target,
                hint=(
                    f"Provide the fields of {describe_type(target)} as "
                    f"JSON-like data."
                ),
            )
    if not isinstance(value, dict):
        return None

    try:
        hints = get_type_hints(target)
    except Exception:
        hints = {}
    build_kwargs = {}
    for field_spec in dataclasses.fields(target):
        if not field_spec.init:
            continue
        if field_spec.name in value:
            field_type = hints.get(field_spec.name, field_spec.type)
            child = replace(
                ctx,
                param_name=f"{ctx.param_name}.{field_spec.name}",
                expected_type=field_type,
                raw_value=value[field_spec.name],
            )
            result = ctx.registry.convert(child)
            if not result.ok:
                return result
            build_kwargs[field_spec.name] = result.value
        elif (
            field_spec.default is dataclasses.MISSING
            and field_spec.default_factory is dataclasses.MISSING
        ):
            return conversion_failure(
                ctx,
                target,
                hint=(
                    f"The data is missing the required field "
                    f"'{field_spec.name}' of {describe_type(target)}."
                ),
            )
    try:
        return ConversionResult(ok=True, value=target(**build_kwargs))
    except Exception:
        return conversion_failure(ctx, target)


def convert_dataclass_to_dict(ctx: ConversionContext) -> Optional[ConversionResult]:
    value = ctx.raw_value
    if dataclasses.is_dataclass(value) and not isinstance(value, type):
        return ConversionResult(ok=True, value=dataclasses.asdict(value))
    return None


_TRUE_STRINGS = {"true", "on", "1", "yes", "checked"}
_FALSE_STRINGS = {"false", "off", "0", "no", ""}


def convert_bool(ctx: ConversionContext) -> Optional[ConversionResult]:
    value = ctx.raw_value
    if isinstance(value, bool):
        return ConversionResult(ok=True, value=value)
    if isinstance(value, str):
        lowered = value.strip().lower()
        if lowered in _TRUE_STRINGS:
            return ConversionResult(ok=True, value=True)
        if lowered in _FALSE_STRINGS:
            return ConversionResult(ok=True, value=False)
        return conversion_failure(
            ctx, bool, hint="Use a checkbox, or a true/false value."
        )
    return None


def convert_int(ctx: ConversionContext) -> Optional[ConversionResult]:
    value = ctx.raw_value
    if isinstance(value, bool):
        return None
    if isinstance(value, str):
        text = value.strip()
        number_hint = (
            "Try entering a number, or change the parameter type to str."
        )
        try:
            return ConversionResult(ok=True, value=int(text))
        except ValueError:
            pass
        try:
            number = float(text)
        except ValueError:
            return conversion_failure(ctx, int, hint=number_hint)
        if number.is_integer():
            return ConversionResult(ok=True, value=int(number))
        return conversion_failure(
            ctx,
            int,
            hint=(
                "This looks like a decimal number; use float instead of int, "
                "or enter a whole number."
            ),
        )
    return None


def convert_float(ctx: ConversionContext) -> Optional[ConversionResult]:
    value = ctx.raw_value
    if isinstance(value, bool):
        return None
    if isinstance(value, str):
        try:
            return ConversionResult(ok=True, value=float(value.strip()))
        except ValueError:
            return conversion_failure(
                ctx,
                float,
                hint="Try entering a number, or change the parameter type to str.",
            )
    return None


def convert_str(ctx: ConversionContext) -> Optional[ConversionResult]:
    value = ctx.raw_value
    if isinstance(value, bytes):
        try:
            return ConversionResult(ok=True, value=value.decode("utf-8"))
        except UnicodeDecodeError:
            return conversion_failure(
                ctx,
                str,
                hint=(
                    "The data is binary, not unicode (utf-8) text; "
                    "use bytes instead of str."
                ),
            )
    return None


def _is_collection_type(target: Any) -> bool:
    return target in _COLLECTION_TYPES


def convert_collection(ctx: ConversionContext) -> Optional[ConversionResult]:
    """Convert to list/tuple/set, wrapping scalars and converting elements."""
    target = ctx.resolved_type
    value = ctx.raw_value
    if isinstance(value, _COLLECTION_TYPES):
        items = list(value)
    else:
        items = [value]

    element_types = tuple(arg for arg in ctx.type_args if arg is not Ellipsis)
    if element_types:
        heterogeneous = (
            target is tuple
            and Ellipsis not in ctx.type_args
            and len(element_types) > 1
        )
        if heterogeneous:
            if len(items) != len(element_types):
                return conversion_failure(
                    ctx,
                    ctx.expected_type,
                    hint=f"Expected exactly {len(element_types)} values.",
                )
            pairs = list(zip(items, element_types))
        else:
            pairs = [(item, element_types[0]) for item in items]
        converted = []
        for index, (item, element_type) in enumerate(pairs):
            child = replace(
                ctx,
                param_name=f"{ctx.param_name}[{index}]",
                expected_type=element_type,
                raw_value=item,
            )
            result = ctx.registry.convert(child)
            if not result.ok:
                return result
            converted.append(result.value)
        items = converted

    if target is list:
        return ConversionResult(ok=True, value=items)
    return ConversionResult(ok=True, value=target(items))


def register_shared_converters(registry: ConverterRegistry) -> None:
    """Install the cross-component converters into a registry."""
    registry.register_predicate(
        _accepts_file_upload, convert_file_upload, priority=10, name="file upload"
    )
    for target in (datetime, date, time):
        registry.register(target, convert_datetime_like, priority=20)
    registry.register_predicate(
        _is_location_type, convert_location, priority=20, name="Location"
    )
    registry.register(dict, convert_dataclass_to_dict, priority=40)
    registry.register_predicate(
        _is_dataclass_type, convert_dataclass, priority=45, name="dataclass"
    )
    registry.register(bool, convert_bool, priority=50)
    registry.register(int, convert_int, priority=50)
    registry.register(float, convert_float, priority=50)
    registry.register(str, convert_str, priority=50)
    registry.register_predicate(
        _is_collection_type, convert_collection, priority=60, name="collection"
    )


#: The shared registry the router uses; components register into this.
CONVERTER_REGISTRY = ConverterRegistry()
register_shared_converters(CONVERTER_REGISTRY)
