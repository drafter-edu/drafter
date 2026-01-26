from dataclasses import dataclass
import html
from drafter.components.page_content import Component, ComponentArgument
from drafter.components.forms import FormComponent
from drafter.components.planning.render_plan import RenderPlan
from typing import Union

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
    for_id: Union[None, str, FormComponent] = None
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
        for_id: Union[None, str, FormComponent] = None,
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
class Progress(Component):
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
    DEFAULT_ATTRS = {"max": 1}

    def __init__(self, value: float, max: float = 1.0, **kwargs):
        self.value = float(value)
        self.max = float(max)
        self.extra_settings = kwargs

    def attributes(self, context) -> dict:
        attributes = super().get_attributes(context)
        attributes["value"] = format_number(self.value)
        if "max" in attributes:
            attributes["max"] = format_number(self.max)
        return attributes
