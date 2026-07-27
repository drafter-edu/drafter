"""A captured photo from a :class:`Camera` component."""

import json
from dataclasses import dataclass
from typing import Literal

from drafter.components.utilities.registry import (
    CONVERTER_REGISTRY,
)
from drafter.data.converter import ConversionContext, ConversionResult
from drafter.data.images import Picture

PhotoStatus = Literal[
    "unavailable", "prompt", "pending", "live", "granted", "denied", "error"
]
"""The permission/capture states a `Photo`'s `status` field can report,
mirroring the camera permission workflow."""


@dataclass
class Photo:
    """A captured photo from a :class:`Camera` component.

    The ``picture`` property provides the captured image as a
    :class:`~drafter.data.images.Picture` value, which can be stored in
    state, manipulated, and handed to
    :class:`~drafter.components.images.Image` or
    :class:`~drafter.components.files.Download`. (The raw ``data_url``
    also still works directly with those components.)

    Attributes:
        status: Current permission/capture state.
        message: Optional descriptive message about the status.
        data_url: The captured photo as a PNG data URL (None if nothing
            has been captured).
        width: Width of the captured photo in pixels (None if unavailable).
        height: Height of the captured photo in pixels (None if unavailable).
    """

    status: PhotoStatus
    message: str | None = None
    data_url: str | None = None
    width: int | None = None
    height: int | None = None

    @property
    def picture(self) -> "Picture | None":
        """The captured photo as a `Picture` value, or None.

        Lazily decoded from ``data_url`` (and cached); None when nothing
        has been captured (check ``status``/``message`` for why).
        """
        if not self.data_url:
            return None
        cached = getattr(self, "_picture", None)
        if cached is None:
            cached = Picture.from_data_url(self.data_url)
            self._picture = cached
        return cached


def _is_photo_type(target) -> bool:
    return target is Photo


def convert_photo(ctx: ConversionContext) -> ConversionResult | None:
    """Convert a JSON string or dict payload into a :class:`Photo`."""
    value = ctx.raw_value
    if isinstance(value, Photo):
        return ConversionResult(ok=True, value=value)
    if isinstance(value, str):
        try:
            value = json.loads(value)
        except json.JSONDecodeError as error:
            # An unparseable photo is a status, not a crash: routes can
            # inspect the error without students needing try/except.
            return ConversionResult(
                ok=True,
                value=Photo(
                    status="error",
                    message=f"Failed to parse photo data: {error}",
                ),
            )
    if isinstance(value, dict):
        try:
            return ConversionResult(ok=True, value=Photo(**value))
        except TypeError as error:
            return ConversionResult(
                ok=True,
                value=Photo(
                    status="error",
                    message=f"Failed to parse photo data: {error}",
                ),
            )
    return None


CONVERTER_REGISTRY.register_predicate(
    _is_photo_type, convert_photo, priority=20, name="Photo"
)
