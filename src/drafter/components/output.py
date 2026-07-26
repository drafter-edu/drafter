"""Output components for displaying computed results and progress.

Defines `Output` (an output element associated with form fields),
`ProgressBar` (an HTML5 progress bar), `Meter` (a gauge within a known
range), and `TimeOutput` (a machine-readable time element).
"""

from dataclasses import dataclass
from datetime import date, time
from datetime import datetime as datetime_type

from drafter.components.forms import FormComponent
from drafter.components.layout import handle_arguments_compatibility
from drafter.components.page_content import Component, ComponentArgument, PageContent
from drafter.components.text import normalize_datetime
from drafter.components.utilities.validation import validate_parameter_name


@dataclass(repr=False)
class Output(FormComponent):
    """Output element for displaying computed or result content.

    Typically used for showing results or responses without user input.

    Attributes:
        name: The output element name for form association.
        content: The content to be displayed.
        for_id: Optional ID of associated form elements.
        tag: The HTML tag name, always 'output'.
    """

    name: str
    content: str
    for_id: None | str | FormComponent = None
    tag = "output"
    KNOWN_ATTRS = ["for", "name"]
    RENAME_ATTRS = {"for_id": "for"}

    ARGUMENTS = [
        ComponentArgument("name"),
        ComponentArgument("content", is_content=True),
        ComponentArgument("for_id", kind="keyword", default_value=None),
    ]

    def __init__(
        self,
        name: str,
        content: str,
        for_id: None | str | FormComponent = None,
        **kwargs,
    ):
        """Initialize output component.

        Args:
            name: The output element name for form association.
            content: The content to display.
            for_id: Optional ID or FormComponent to associate with.
            **kwargs: Additional HTML attributes.

        Raises:
            ValueError: If name is not a valid parameter name.
        """
        validate_parameter_name(name, "Output")
        self.name = name
        self.content = content
        if isinstance(for_id, FormComponent):
            for_id = for_id.get_id()
        self.for_id = for_id
        self.extra_settings = kwargs


def format_number(num):
    """Format a number, removing decimal point for integers.

    Args:
        num: The number to format.

    Returns:
        String representation of the number.
    """
    if num == int(num):
        return str(int(num))
    return str(num)


@dataclass(repr=False)
class ProgressBar(Component):
    """HTML5 progress bar element for showing task completion.

    Attributes:
        value: Current progress value (typically 0 to max).
        max: Maximum value for the progress bar.
        tag: The HTML tag name, always 'progress'.
    """

    value: float
    max: float

    tag = "progress"
    KNOWN_ATTRS = ["value", "max"]
    DEFAULT_ATTRS = {"max": 1}

    ARGUMENTS = [
        ComponentArgument("value"),
        ComponentArgument("max", kind="keyword", default_value=1.0),
    ]

    def __init__(self, value: float, max: float = 1.0, **kwargs):
        """Initialize progress component.

        Args:
            value: Current progress value.
            max: Maximum value. Defaults to 1.0.
            **kwargs: Additional HTML attributes and styles.
        """
        self.value = value
        self.max = max
        self.extra_settings = kwargs

    def get_attributes(self, context) -> dict:
        """Build HTML attributes with numerically formatted value and max.

        Formats `value` (and `max`, when present) via `format_number` so
        that whole numbers render without a trailing decimal point.

        Args:
            context: Rendering context.

        Returns:
            Dictionary of HTML attributes with formatted value and max.
        """
        attributes = super().get_attributes(context)
        attributes["value"] = format_number(self.value)
        if "max" in attributes:
            attributes["max"] = format_number(self.max)
        return attributes


@dataclass(repr=False)
class Meter(Component):
    """HTML5 meter element for showing a value within a known range.

    Unlike `ProgressBar` (which shows task completion), a meter is a
    gauge for a measurement like disk usage or a test score. Browsers
    color the bar based on the low/high/optimum thresholds.

    Attributes:
        value: The measured value.
        min: Lower bound of the range (browser default 0).
        max: Upper bound of the range (browser default 1).
        low: Upper bound of the "low" portion of the range.
        high: Lower bound of the "high" portion of the range.
        optimum: The optimal value within the range.
        tag: The HTML tag name, always 'meter'.

    Example:
        ```python
        Meter(70, min=0, max=100, low=30, high=80, optimum=90)
        ```
    """

    value: float
    min: float | None
    max: float | None
    low: float | None
    high: float | None
    optimum: float | None

    tag = "meter"
    KNOWN_ATTRS = ["value", "min", "max", "low", "high", "optimum"]

    ARGUMENTS = [
        ComponentArgument("value"),
        ComponentArgument("min", kind="keyword", default_value=None),
        ComponentArgument("max", kind="keyword", default_value=None),
        ComponentArgument("low", kind="keyword", default_value=None),
        ComponentArgument("high", kind="keyword", default_value=None),
        ComponentArgument("optimum", kind="keyword", default_value=None),
    ]

    def __init__(
        self,
        value: float,
        min: float | None = None,
        max: float | None = None,
        low: float | None = None,
        high: float | None = None,
        optimum: float | None = None,
        **kwargs,
    ):
        """Initialize meter component.

        Args:
            value: The measured value.
            min: Lower bound of the range.
            max: Upper bound of the range.
            low: Upper bound of the "low" portion of the range.
            high: Lower bound of the "high" portion of the range.
            optimum: The optimal value within the range.
            **kwargs: Additional HTML attributes and styles.
        """
        self.value = value
        self.min = min
        self.max = max
        self.low = low
        self.high = high
        self.optimum = optimum
        self.extra_settings = kwargs

    def get_attributes(self, context) -> dict:
        """Build HTML attributes with numerically formatted range values.

        Formats each numeric attribute via `format_number` so that whole
        numbers render without a trailing decimal point.

        Args:
            context: Rendering context.

        Returns:
            Dictionary of HTML attributes with formatted numeric values.
        """
        attributes = super().get_attributes(context)
        for key in self.KNOWN_ATTRS:
            if key in attributes and isinstance(attributes[key], (int, float)):
                attributes[key] = format_number(attributes[key])
        return attributes


@dataclass(repr=False)
class TimeOutput(Component):
    """Renders a time element with an optional machine-readable datetime.

    Attributes:
        content: List of page content items showing the human-readable time.
        datetime: The machine-readable ISO form of the time, if any.
        tag: The HTML tag name, always 'time'.

    Example:
        ```python
        TimeOutput("July 25th", datetime="2026-07-25")
        ```
    """

    content: list[PageContent]
    datetime: str | None
    tag = "time"

    KNOWN_ATTRS = ["datetime"]
    ARGUMENTS = [
        ComponentArgument("content", kind="var", is_content=True),
        ComponentArgument("datetime", kind="keyword", default_value=None),
    ]

    def __init__(
        self,
        *content: PageContent,
        datetime: str | datetime_type | date | time | None = None,
        **extra_settings,
    ):
        """Initialize time output component.

        Args:
            *content: Variable-length human-readable time content.
            datetime: The machine-readable form; datetime/date/time objects
                are converted to their ISO string form.
            **extra_settings: Additional HTML attributes and styles.
        """
        self.content, self.extra_settings = handle_arguments_compatibility(
            list(content), extra_settings
        )
        self.datetime = normalize_datetime(datetime)
