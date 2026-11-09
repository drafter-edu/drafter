"""Colors as values: the `Color` data type and the ways to write one.

A color can reach Drafter in several spellings: a hex code (`"#ff8800"`,
or the short form `"#f80"`), one of the browser's color names
(`"tomato"`), a list of red, green, and blue numbers (`[255, 136, 0]`),
or a `Color` value. `to_color` turns any of them into a `Color`, which is
what `ColorPicker` uses for its starting color and what the route
parameter converters (registered at the bottom of this module) use to
hand a picked color to a route as a `Color` or a `list[int]`.

Every channel is a whole number from 0 to 255, including `alpha`
(0 is fully see-through, 255 is solid). That matches the `(red, green,
blue, alpha)` pixels of a `Picture`, so colors and pixels can be mixed
without converting between scales.
"""

import difflib
import re
from dataclasses import dataclass
from typing import Any

from drafter.data.converter import (
    COLLECTION_TYPES,
    CONVERTER_REGISTRY,
    ConversionContext,
    ConversionResult,
    conversion_failure,
)
from drafter.data.errors import StudentFacingError

CSS_COLOR_NAMES: dict[str, str] = {
    "aliceblue": "#f0f8ff",
    "antiquewhite": "#faebd7",
    "aqua": "#00ffff",
    "aquamarine": "#7fffd4",
    "azure": "#f0ffff",
    "beige": "#f5f5dc",
    "bisque": "#ffe4c4",
    "black": "#000000",
    "blanchedalmond": "#ffebcd",
    "blue": "#0000ff",
    "blueviolet": "#8a2be2",
    "brown": "#a52a2a",
    "burlywood": "#deb887",
    "cadetblue": "#5f9ea0",
    "chartreuse": "#7fff00",
    "chocolate": "#d2691e",
    "coral": "#ff7f50",
    "cornflowerblue": "#6495ed",
    "cornsilk": "#fff8dc",
    "crimson": "#dc143c",
    "cyan": "#00ffff",
    "darkblue": "#00008b",
    "darkcyan": "#008b8b",
    "darkgoldenrod": "#b8860b",
    "darkgray": "#a9a9a9",
    "darkgreen": "#006400",
    "darkgrey": "#a9a9a9",
    "darkkhaki": "#bdb76b",
    "darkmagenta": "#8b008b",
    "darkolivegreen": "#556b2f",
    "darkorange": "#ff8c00",
    "darkorchid": "#9932cc",
    "darkred": "#8b0000",
    "darksalmon": "#e9967a",
    "darkseagreen": "#8fbc8f",
    "darkslateblue": "#483d8b",
    "darkslategray": "#2f4f4f",
    "darkslategrey": "#2f4f4f",
    "darkturquoise": "#00ced1",
    "darkviolet": "#9400d3",
    "deeppink": "#ff1493",
    "deepskyblue": "#00bfff",
    "dimgray": "#696969",
    "dimgrey": "#696969",
    "dodgerblue": "#1e90ff",
    "firebrick": "#b22222",
    "floralwhite": "#fffaf0",
    "forestgreen": "#228b22",
    "fuchsia": "#ff00ff",
    "gainsboro": "#dcdcdc",
    "ghostwhite": "#f8f8ff",
    "gold": "#ffd700",
    "goldenrod": "#daa520",
    "gray": "#808080",
    "green": "#008000",
    "greenyellow": "#adff2f",
    "grey": "#808080",
    "honeydew": "#f0fff0",
    "hotpink": "#ff69b4",
    "indianred": "#cd5c5c",
    "indigo": "#4b0082",
    "ivory": "#fffff0",
    "khaki": "#f0e68c",
    "lavender": "#e6e6fa",
    "lavenderblush": "#fff0f5",
    "lawngreen": "#7cfc00",
    "lemonchiffon": "#fffacd",
    "lightblue": "#add8e6",
    "lightcoral": "#f08080",
    "lightcyan": "#e0ffff",
    "lightgoldenrodyellow": "#fafad2",
    "lightgray": "#d3d3d3",
    "lightgreen": "#90ee90",
    "lightgrey": "#d3d3d3",
    "lightpink": "#ffb6c1",
    "lightsalmon": "#ffa07a",
    "lightseagreen": "#20b2aa",
    "lightskyblue": "#87cefa",
    "lightslategray": "#778899",
    "lightslategrey": "#778899",
    "lightsteelblue": "#b0c4de",
    "lightyellow": "#ffffe0",
    "lime": "#00ff00",
    "limegreen": "#32cd32",
    "linen": "#faf0e6",
    "magenta": "#ff00ff",
    "maroon": "#800000",
    "mediumaquamarine": "#66cdaa",
    "mediumblue": "#0000cd",
    "mediumorchid": "#ba55d3",
    "mediumpurple": "#9370db",
    "mediumseagreen": "#3cb371",
    "mediumslateblue": "#7b68ee",
    "mediumspringgreen": "#00fa9a",
    "mediumturquoise": "#48d1cc",
    "mediumvioletred": "#c71585",
    "midnightblue": "#191970",
    "mintcream": "#f5fffa",
    "mistyrose": "#ffe4e1",
    "moccasin": "#ffe4b5",
    "navajowhite": "#ffdead",
    "navy": "#000080",
    "oldlace": "#fdf5e6",
    "olive": "#808000",
    "olivedrab": "#6b8e23",
    "orange": "#ffa500",
    "orangered": "#ff4500",
    "orchid": "#da70d6",
    "palegoldenrod": "#eee8aa",
    "palegreen": "#98fb98",
    "paleturquoise": "#afeeee",
    "palevioletred": "#db7093",
    "papayawhip": "#ffefd5",
    "peachpuff": "#ffdab9",
    "peru": "#cd853f",
    "pink": "#ffc0cb",
    "plum": "#dda0dd",
    "powderblue": "#b0e0e6",
    "purple": "#800080",
    "rebeccapurple": "#663399",
    "red": "#ff0000",
    "rosybrown": "#bc8f8f",
    "royalblue": "#4169e1",
    "saddlebrown": "#8b4513",
    "salmon": "#fa8072",
    "sandybrown": "#f4a460",
    "seagreen": "#2e8b57",
    "seashell": "#fff5ee",
    "sienna": "#a0522d",
    "silver": "#c0c0c0",
    "skyblue": "#87ceeb",
    "slateblue": "#6a5acd",
    "slategray": "#708090",
    "slategrey": "#708090",
    "snow": "#fffafa",
    "springgreen": "#00ff7f",
    "steelblue": "#4682b4",
    "tan": "#d2b48c",
    "teal": "#008080",
    "thistle": "#d8bfd8",
    "tomato": "#ff6347",
    "turquoise": "#40e0d0",
    "violet": "#ee82ee",
    "wheat": "#f5deb3",
    "white": "#ffffff",
    "whitesmoke": "#f5f5f5",
    "yellow": "#ffff00",
    "yellowgreen": "#9acd32",
}
"""The 148 color names every browser understands, mapped to their
`#rrggbb` hex codes (lowercase). Both spellings of gray (`gray` and
`grey`) are included wherever CSS defines both."""

TRANSPARENT_NAME = "transparent"
"""The one CSS color keyword that is not a solid color: black with an
alpha of zero."""

HEX_COLOR_PATTERN = re.compile(r"#(?:[0-9a-fA-F]{3,4}|[0-9a-fA-F]{6}|[0-9a-fA-F]{8})")
"""A hash sign followed by 3, 4, 6, or 8 hexadecimal digits. The 3- and
4-digit forms are shorthand in which every digit is doubled (`#f80` means
`#ff8800`); the 4- and 8-digit forms end with the alpha channel."""

CHANNEL_NAMES = ("red", "green", "blue", "alpha")
"""The `Color` fields, in the order they appear in a list or hex code."""


@dataclass
class Color:
    """A color, stored as red, green, blue, and alpha amounts.

    Each amount is a whole number from 0 (none) to 255 (full). `alpha` is
    how solid the color is: 255 is completely solid and 0 is invisible.

    Printing a `Color`, or using it where Drafter expects a color (such as
    `style_color` or `change_background_color`), gives its hex code.

    Attributes:
        red: Amount of red, from 0 to 255.
        green: Amount of green, from 0 to 255.
        blue: Amount of blue, from 0 to 255.
        alpha: How solid the color is, from 0 (invisible) to 255 (solid).

    Example:
        ```python
        orange = Color(255, 136, 0)
        Span("Hello", style_color=orange)
        ```
    """

    red: int
    green: int
    blue: int
    alpha: int = 255

    def __post_init__(self) -> None:
        """Check that every channel is a whole number from 0 to 255.

        Raises:
            StudentFacingError: If a channel is not a whole number, or is
                outside the range 0 to 255.
        """
        for channel in CHANNEL_NAMES:
            value = getattr(self, channel)
            if isinstance(value, float) and value == int(value):
                value = int(value)
                setattr(self, channel, value)
            if isinstance(value, bool) or not isinstance(value, int):
                raise StudentFacingError(
                    f"Color {channel} must be a whole number from 0 to 255, "
                    f"but got {value!r} ({type(value).__name__}).",
                    friendly=(
                        f"The {channel} amount of a color has to be a whole "
                        f"number from 0 to 255, but it was {value!r}."
                    ),
                    steps=(
                        "Use whole numbers, like Color(255, 136, 0).",
                        "If you have a fraction from 0 to 1, multiply it by "
                        "255 and round it first.",
                    ),
                )
            if not 0 <= value <= 255:
                raise StudentFacingError(
                    f"Color {channel} must be from 0 to 255, but got {value!r}.",
                    friendly=(
                        f"The {channel} amount of a color goes from 0 (none) "
                        f"to 255 (full), but it was {value!r}."
                    ),
                    steps=("Keep each amount between 0 and 255.",),
                )

    def to_hex(self, alpha: bool | None = None) -> str:
        """Write the color as a hex code.

        Args:
            alpha: Whether to include the alpha channel as two extra
                digits. Defaults to None, which includes it only when the
                color is not fully solid.

        Returns:
            The lowercase hex code: `#rrggbb`, or `#rrggbbaa` with alpha.

        Example:
            ```python
            Color(255, 136, 0).to_hex()  # "#ff8800"
            ```
        """
        if alpha is None:
            alpha = self.alpha != 255
        channels = [self.red, self.green, self.blue]
        if alpha:
            channels.append(self.alpha)
        return "#" + "".join(f"{channel:02x}" for channel in channels)

    def to_list(self, alpha: bool | None = None) -> list[int]:
        """Give the color's amounts as a list of whole numbers.

        Args:
            alpha: Whether to include the alpha amount as a fourth item.
                Defaults to None, which includes it only when the color is
                not fully solid.

        Returns:
            `[red, green, blue]`, or `[red, green, blue, alpha]`.
        """
        if alpha is None:
            alpha = self.alpha != 255
        channels = [self.red, self.green, self.blue]
        if alpha:
            channels.append(self.alpha)
        return channels

    def __str__(self) -> str:
        """The hex code, so a Color works wherever CSS expects a color."""
        return self.to_hex()

    @classmethod
    def from_hex(cls, code: str) -> "Color":
        """Build a color from a hex code.

        Args:
            code: A hash sign and 3, 4, 6, or 8 hex digits, such as
                `"#ff8800"`, `"#f80"`, or `"#ff880080"`.

        Returns:
            The matching Color.

        Raises:
            StudentFacingError: If the text is not a hex color code.

        Example:
            ```python
            Color.from_hex("#f80")  # Color(red=255, green=136, blue=0, alpha=255)
            ```
        """
        if not isinstance(code, str) or not HEX_COLOR_PATTERN.fullmatch(code.strip()):
            raise _unreadable_color(code)
        digits = code.strip()[1:]
        if len(digits) in (3, 4):
            digits = "".join(digit * 2 for digit in digits)
        channels = [
            int(digits[index : index + 2], 16) for index in range(0, len(digits), 2)
        ]
        return cls(*channels)

    @classmethod
    def from_name(cls, name: str) -> "Color":
        """Build a color from one of the browser's color names.

        Args:
            name: A CSS color name such as `"tomato"` or `"Steel Blue"`.
                Capital letters and spaces are ignored.

        Returns:
            The matching Color.

        Raises:
            StudentFacingError: If the name is not a browser color name.

        Example:
            ```python
            Color.from_name("tomato")  # Color(red=255, green=99, blue=71, alpha=255)
            ```
        """
        key = _normalize_name(name) if isinstance(name, str) else ""
        if key == TRANSPARENT_NAME:
            return cls(0, 0, 0, 0)
        if key not in CSS_COLOR_NAMES:
            raise _unreadable_color(name)
        return cls.from_hex(CSS_COLOR_NAMES[key])


def _normalize_name(name: str) -> str:
    """Lowercase a color name and drop spaces, hyphens, and underscores."""
    return re.sub(r"[\s_-]+", "", name).lower()


def _suggest_names(name: str) -> list[str]:
    """Color names close to a misspelled one, best match first."""
    return difflib.get_close_matches(
        _normalize_name(name), list(CSS_COLOR_NAMES), n=3, cutoff=0.7
    )


def _unreadable_color(value: Any) -> StudentFacingError:
    """The error for a value that is not any recognized color spelling.

    Args:
        value: What was given where a color was expected.

    Returns:
        A StudentFacingError explaining the accepted spellings, with
        suggestions when the value looks like a misspelled color name.
    """
    steps = [
        "Write a hex code such as '#ff8800' (or the short form '#f80').",
        "Or use a color name such as 'tomato' or 'steelblue'.",
        "Or give the red, green, and blue amounts as a list, like [255, 136, 0].",
    ]
    if isinstance(value, str) and value and not value.strip().startswith("#"):
        suggestions = _suggest_names(value)
        if suggestions:
            steps.insert(
                0,
                "Did you mean "
                + " or ".join(f"'{name}'" for name in suggestions)
                + "?",
            )
    return StudentFacingError(
        f"Could not read {value!r} as a color.",
        friendly=(
            f"Drafter expected a color but got {value!r}, which is not a hex "
            "code, a color name it knows, or a list of red, green, and blue "
            "amounts."
        ),
        steps=tuple(steps),
    )


def to_color(value: Any) -> Color:
    """Turn any accepted spelling of a color into a `Color`.

    Args:
        value: A `Color`; a hex code (`"#ff8800"`, `"#f80"`, with an
            optional alpha part); a browser color name (`"tomato"`); or a
            list or tuple of three or four whole numbers from 0 to 255
            (red, green, blue, and optionally alpha).

    Returns:
        The matching Color (the same object when given a Color).

    Raises:
        StudentFacingError: If the value is not a recognizable color.

    Example:
        ```python
        to_color("#f80")  # Color(255, 136, 0)
        to_color("tomato")  # Color(255, 99, 71)
        to_color([255, 136, 0])  # Color(255, 136, 0)
        ```
    """
    if isinstance(value, Color):
        return value
    if isinstance(value, str):
        if value.strip().startswith("#"):
            return Color.from_hex(value)
        return Color.from_name(value)
    if isinstance(value, (list, tuple)):
        if len(value) not in (3, 4):
            raise StudentFacingError(
                f"A color list needs 3 or 4 numbers, but got {len(value)}: {value!r}.",
                friendly=(
                    "A color written as a list needs three numbers (red, "
                    "green, blue) or four (with alpha at the end), but this "
                    f"one has {len(value)}."
                ),
                steps=("Give red, green, and blue, like [255, 136, 0].",),
            )
        return Color(*value)
    if isinstance(value, dict) and {"red", "green", "blue"} <= set(value):
        return Color(
            value["red"], value["green"], value["blue"], value.get("alpha", 255)
        )
    raise _unreadable_color(value)


def _is_color_type(target: Any) -> bool:
    return target is Color


def convert_color(ctx: ConversionContext) -> ConversionResult | None:
    """Convert a submitted color (hex code, name, list, or dict) to a `Color`."""
    try:
        return ConversionResult(ok=True, value=to_color(ctx.raw_value))
    except StudentFacingError as error:
        return conversion_failure(
            ctx, Color, hint=" ".join(error.friendly_steps) or str(error)
        )


def _wants_whole_numbers(ctx: ConversionContext) -> bool:
    """Whether the target is a collection annotated to hold only ints."""
    element_types = tuple(arg for arg in ctx.type_args if arg is not Ellipsis)
    return bool(element_types) and all(arg is int for arg in element_types)


def convert_hex_color_to_numbers(ctx: ConversionContext) -> ConversionResult | None:
    """Convert a submitted hex color to a collection of whole numbers.

    A `ColorPicker` submits text such as `"#ff8800"`. When the route asks
    for `list[int]` (or a tuple or set of ints), that text becomes the
    red, green, and blue amounts, plus alpha when the code includes it.
    Anything that is not a hex color code is left for the ordinary
    collection converter.
    """
    value = ctx.raw_value
    if isinstance(value, list) and len(value) == 1:
        value = value[0]
    if not isinstance(value, str) or not HEX_COLOR_PATTERN.fullmatch(value.strip()):
        return None
    if not _wants_whole_numbers(ctx):
        return None
    color = Color.from_hex(value)
    has_alpha = len(value.strip()) in (5, 9)
    numbers = color.to_list(alpha=has_alpha)
    target = ctx.resolved_type
    fixed_length = [arg for arg in ctx.type_args if arg is not Ellipsis]
    if target is tuple and Ellipsis not in ctx.type_args and len(fixed_length) > 1:
        if len(fixed_length) != len(numbers):
            return conversion_failure(
                ctx,
                ctx.expected_type,
                hint=(
                    f"This color has {len(numbers)} amounts, so annotate the "
                    f"parameter with {len(numbers)} ints, or use list[int]."
                ),
            )
    if target is list:
        return ConversionResult(ok=True, value=numbers)
    return ConversionResult(ok=True, value=target(numbers))


def _is_collection_type(target: Any) -> bool:
    return target in COLLECTION_TYPES


# Color runs before the generic dataclass converter (priority 45), which
# only understands dicts. The hex-to-numbers converter runs before the
# generic collection converter (priority 60), which would otherwise wrap
# the text in a one-item list and fail to turn it into an int.
CONVERTER_REGISTRY.register_predicate(
    _is_color_type, convert_color, priority=20, name="Color"
)
CONVERTER_REGISTRY.register_predicate(
    _is_collection_type,
    convert_hex_color_to_numbers,
    priority=55,
    name="hex color to numbers",
)
