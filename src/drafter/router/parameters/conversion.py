"""
Shared type converters for route parameters.

The conversion machinery (:class:`ConverterRegistry`, the shared
:data:`CONVERTER_REGISTRY` instance, and the failure helpers) lives in
:mod:`drafter.data.converter` so both the component and router layers can
import it eagerly. This module owns conversion *policy*: it installs the
cross-component converters (files, datetime, images, dataclasses, scalars,
collections) into the shared registry when the router loads. Components
contribute component-specific converters (e.g. ``Location`` in
:mod:`drafter.components.geolocation`) by registering into the same
registry, conventionally imported via
``drafter.components.utilities.registry``.
"""

import dataclasses
import inspect
import io
import json
from dataclasses import replace
from datetime import date, datetime, time
from typing import Any, get_type_hints

from PIL import Image as PILImage

from drafter.data.converter import (
    COLLECTION_TYPES,
    CONVERTER_REGISTRY,
    ConversionContext,
    ConversionResult,
    ConverterRegistry,
    conversion_failure,
    describe_type,
    missing_value_failure,
    preview_value,
)
from drafter.data.files import DrafterBinaryFile, DrafterTextFile
from drafter.data.images import Picture, decode_data_url
from drafter.helpers.dates import try_convert_datetime

__all__ = [
    "CONVERTER_REGISTRY",
    "ConverterRegistry",
    "conversion_failure",
    "describe_type",
    "preview_value",
    "register_shared_converters",
]


# --- Shared converters -------------------------------------------------------
# Cross-component types are first-class here so no component duplicates them.


def _accepts_file_upload(target: Any) -> bool:
    try:
        if target in (bytes, str, dict, DrafterBinaryFile, DrafterTextFile):
            return True
    except TypeError:
        return False
    return inspect.isclass(target) and issubclass(target, PILImage.Image)


def convert_file_upload(ctx: ConversionContext) -> ConversionResult | None:
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

    if inspect.isclass(target) and issubclass(target, PILImage.Image):
        # Back-compat: PIL annotations still work, but docs teach Picture.
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


def _is_picture_type(target: Any) -> bool:
    return target is Picture


def _camera_status_hint(value: dict, target: Any) -> str:
    status = value.get("status", "unknown")
    message = value.get("message") or ""
    detail = f" ({message})" if message else ""
    return (
        f"The camera did not provide a photo (status: {status}{detail}). "
        f"Annotate the parameter as Photo to inspect the status, or as "
        f"{describe_type(target)} | None to receive None instead."
    )


def convert_picture(ctx: ConversionContext) -> ConversionResult | None:
    """Convert any supported image payload to a :class:`Picture`.

    Accepts file-upload dicts, camera-style dicts (with a ``data_url``),
    data URL / URL / path strings, raw bytes, PIL images, ``Photo``
    envelopes, and existing Pictures. Empty uploads and photo-less camera
    payloads fail with a missing-value error, which union conversion turns
    into None for ``Picture | None`` annotations.
    """
    value = ctx.raw_value
    if isinstance(value, Picture):
        return ConversionResult(ok=True, value=value)
    if isinstance(value, PILImage.Image):
        return ConversionResult(ok=True, value=Picture(value))

    if isinstance(value, str):
        stripped = value.strip()
        if not stripped:
            return missing_value_failure(ctx, Picture)
        if stripped.startswith("{"):
            try:
                value = json.loads(stripped)
            except json.JSONDecodeError:
                return conversion_failure(ctx, Picture)
        elif stripped.startswith("data:"):
            try:
                return ConversionResult(ok=True, value=Picture.from_data_url(stripped))
            except Exception:
                return conversion_failure(
                    ctx,
                    Picture,
                    hint="The data URL could not be decoded as an image.",
                )
        elif stripped.startswith(("http://", "https://")):
            return ConversionResult(ok=True, value=Picture.from_url(stripped))
        else:
            try:
                return ConversionResult(ok=True, value=Picture(stripped))
            except Exception as error:
                return conversion_failure(
                    ctx,
                    Picture,
                    hint=f"Could not open {stripped!r} as an image: {error}",
                )

    if isinstance(value, (bytes, bytearray)):
        try:
            return ConversionResult(ok=True, value=Picture.from_bytes(bytes(value)))
        except Exception:
            return conversion_failure(
                ctx,
                Picture,
                hint="The binary data could not be decoded as an image.",
            )

    if isinstance(value, dict):
        if value.get("__file_upload__"):
            content = value.get("content", b"")
            filename = value.get("filename", None)
            if not content:
                return missing_value_failure(
                    ctx,
                    Picture,
                    hint=(
                        "No file was chosen. Did you mean to make the "
                        "parameter optional (Picture | None)?"
                    ),
                )
            try:
                return ConversionResult(
                    ok=True,
                    value=Picture.from_bytes(
                        content, filename=filename, mime_type=value.get("type")
                    ),
                )
            except Exception:
                return conversion_failure(
                    ctx,
                    Picture,
                    hint=(
                        f"Could not open {filename!r} as an image. Perhaps "
                        f"the file is not an image?"
                    ),
                )
        if "data_url" in value:
            data_url = value.get("data_url")
            if not data_url:
                return missing_value_failure(
                    ctx, Picture, hint=_camera_status_hint(value, Picture)
                )
            try:
                return ConversionResult(ok=True, value=Picture.from_data_url(data_url))
            except Exception:
                return conversion_failure(
                    ctx,
                    Picture,
                    hint="The captured photo could not be decoded as an image.",
                )

    # A Photo (or compatible camera envelope) converts to its image.
    if hasattr(value, "status") and hasattr(value, "data_url"):
        if not value.data_url:
            return missing_value_failure(
                ctx,
                Picture,
                hint=_camera_status_hint(
                    {"status": value.status, "message": value.message}, Picture
                ),
            )
        try:
            return ConversionResult(ok=True, value=Picture(value))
        except Exception:
            return conversion_failure(
                ctx,
                Picture,
                hint="The captured photo could not be decoded as an image.",
            )
    return None


def convert_camera_bytes(ctx: ConversionContext) -> ConversionResult | None:
    """Convert camera-style payloads to raw encoded image bytes.

    Lets ``bytes`` annotations work for :class:`Camera` fields the same way
    they already do for uploads: a camera dict (or bare data URL string)
    becomes the decoded PNG bytes. Payloads without a photo fail with a
    missing-value error (None for ``bytes | None`` annotations).
    """
    value = ctx.raw_value
    if isinstance(value, str) and value.startswith("data:"):
        try:
            data, _ = decode_data_url(value)
            return ConversionResult(ok=True, value=data)
        except ValueError:
            return conversion_failure(
                ctx, bytes, hint="The data URL could not be decoded."
            )
    if isinstance(value, dict) and "data_url" in value and "content" not in value:
        data_url = value.get("data_url")
        if not data_url:
            return missing_value_failure(
                ctx, bytes, hint=_camera_status_hint(value, bytes)
            )
        try:
            data, _ = decode_data_url(data_url)
            return ConversionResult(ok=True, value=data)
        except ValueError:
            return conversion_failure(
                ctx, bytes, hint="The captured photo could not be decoded."
            )
    return None


def convert_datetime_like(ctx: ConversionContext) -> ConversionResult | None:
    """Convert ISO-formatted strings to ``datetime``, ``date``, or ``time``.

    Delegates to ``try_convert_datetime``; unparseable values fail with a
    hint to use an ISO format, and unhandled value/target combinations
    defer to the next converter.
    """
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


def _is_dataclass_type(target: Any) -> bool:
    return isinstance(target, type) and dataclasses.is_dataclass(target)


def convert_dataclass(ctx: ConversionContext) -> ConversionResult | None:
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
                    f"Provide the fields of {describe_type(target)} as JSON-like data."
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


def convert_dataclass_to_dict(ctx: ConversionContext) -> ConversionResult | None:
    """Convert a dataclass instance to a plain dict via ``dataclasses.asdict``."""
    value = ctx.raw_value
    if dataclasses.is_dataclass(value) and not isinstance(value, type):
        return ConversionResult(ok=True, value=dataclasses.asdict(value))
    return None


_TRUE_STRINGS = {"true", "on", "1", "yes", "checked"}
_FALSE_STRINGS = {"false", "off", "0", "no", ""}


def convert_bool(ctx: ConversionContext) -> ConversionResult | None:
    """Convert checkbox-style strings to bool.

    Existing bools pass through. Strings are stripped and lowercased, then
    matched against the truthy set ("true", "on", "1", "yes", "checked")
    and the falsy set ("false", "off", "0", "no", and the empty string);
    any other string fails with a hint to use a checkbox or true/false
    value. Non-string, non-bool values defer to the next converter.
    """
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


def convert_int(ctx: ConversionContext) -> ConversionResult | None:
    """Convert numeric strings to int.

    Strings are stripped and parsed with ``int``; if that fails, they are
    parsed as floats and accepted only when the result is a whole number.
    Decimal values fail with a hint to use float instead, and non-numeric
    strings fail with a hint to enter a number or use str. Bools and
    non-string values defer to the next converter.
    """
    value = ctx.raw_value
    if isinstance(value, bool):
        return None
    if isinstance(value, str):
        text = value.strip()
        number_hint = "Try entering a number, or change the parameter type to str."
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


def convert_float(ctx: ConversionContext) -> ConversionResult | None:
    """Convert numeric strings to float.

    Strings are stripped and parsed with ``float``; non-numeric strings
    fail with a hint to enter a number or use str. Bools and non-string
    values defer to the next converter.
    """
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


def convert_str(ctx: ConversionContext) -> ConversionResult | None:
    """Decode bytes values to str as UTF-8.

    Non-UTF-8 bytes fail with a hint to use bytes instead of str; all
    other values defer to the registry's default string handling.
    """
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
    return target in COLLECTION_TYPES


def convert_collection(ctx: ConversionContext) -> ConversionResult | None:
    """Convert to list/tuple/set, wrapping scalars and converting elements."""
    target = ctx.resolved_type
    value = ctx.raw_value
    if isinstance(value, COLLECTION_TYPES):
        items = list(value)
    else:
        items = [value]

    element_types = tuple(arg for arg in ctx.type_args if arg is not Ellipsis)
    if element_types:
        heterogeneous = (
            target is tuple and Ellipsis not in ctx.type_args and len(element_types) > 1
        )
        if heterogeneous:
            if len(items) != len(element_types):
                return conversion_failure(
                    ctx,
                    ctx.expected_type,
                    hint=f"Expected exactly {len(element_types)} values.",
                )
            pairs = list(zip(items, element_types, strict=True))
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
    registry.register_predicate(
        _is_picture_type, convert_picture, priority=20, name="Picture"
    )
    registry.register(bytes, convert_camera_bytes, priority=30, name="camera bytes")
    for target in (datetime, date, time):
        registry.register(target, convert_datetime_like, priority=20)
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


register_shared_converters(CONVERTER_REGISTRY)
