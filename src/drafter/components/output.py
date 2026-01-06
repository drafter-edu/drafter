from dataclasses import dataclass
import html
from drafter.components.page_content import Component, ComponentArgument
from drafter.components.forms import FormComponent
from drafter.components.planning.render_plan import RenderPlan
from typing import Union

from drafter.components.utilities.validation import validate_parameter_name


@dataclass(repr=False)
class Output(FormComponent):
    """
    A component to display output content, typically used for showing results or responses.

    Args:
        content: The content to be displayed as output.
        **kwargs: Additional HTML attributes.
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
        validate_parameter_name(name, "Output")
        self.name = name
        self.content = content
        if isinstance(for_id, FormComponent):
            for_id = for_id.get_id()
        self.for_id = for_id
        self.extra_settings = kwargs


def format_number(num):
    if num == int(num):
        return str(int(num))
    return str(num)


@dataclass(repr=False)
class Progress(Component):
    """
    HTML5 progress bar element for showing task completion.

    Args:
        value: Current progress value (typically 0-max)
        max: Maximum value (default: 1)
        **kwargs: Additional HTML attributes

    Example:
        Progress(0.5, max=1)  # 50% progress bar
        Progress(0.6, max=1, style_width="200px")  # 60% progress, custom width
    """

    value: float
    max: float

    tag = "progress"
    KNOWN_ATTRS = ["value", "max"]

    ARGUMENTS = [
        ComponentArgument("value"),
        ComponentArgument("max", kind="keyword", default_value=1.0),
    ]
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
