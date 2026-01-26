from dataclasses import dataclass
from datetime import datetime, date, time
import html
from typing import List, Optional, Union, Any
from drafter.components.page_content import Component, ComponentArgument, PageContent
from drafter.components.planning.render_plan import RenderPlan
from drafter.components.utilities.validation import validate_parameter_name


class FormComponent(Component):
    """Base class for form input components.

    Provides shared functionality for form fields including ARIA labels
    and ID management.

    Attributes:
        name: The form field name for parameter submission.
    """

    name: str

    def handle_aria(self, attributes: dict) -> None:
        """Add ARIA label attribute if not already present.

        Args:
            attributes: Dictionary of HTML attributes to update.
        """
        if "aria-label" not in attributes:
            attributes["aria-label"] = self.name

    def get_attributes(self, context) -> dict:
        """Get HTML attributes for the form component.

        Args:
            context: Rendering context.

        Returns:
            Dictionary of HTML attributes including ARIA label.
        """
        attrs = super().get_attributes(context)
        self.handle_aria(attrs)
        return attrs

    def get_id(self) -> str:
        """Get the identifier for this form field.

        Returns:
            The element ID or the field name.
        """
        return self.extra_settings.get("id", self.name)


@dataclass(repr=False)
class Label(Component):
    """A label element for form fields, optionally associated with an input.

    Attributes:
        text: The label text content.
        for_id: Optional ID or FormComponent to associate with this label.
        tag: The HTML tag name, always 'label'.
    """

    text: str
    for_id: Union[None, str, FormComponent] = None
    tag = "label"

    ARGUMENTS = [
        ComponentArgument("text", is_content=True),
        ComponentArgument("for_id", kind="keyword", default_value=None),
    ]

    KNOWN_ATTRS = ["for"]
    RENAME_ATTRS = {"for_id": "for"}

    def __init__(
        self,
        text: str,
        for_id: Union[None, str, FormComponent] = None,
        **extra_settings,
    ):
        """Initialize label component.

        Args:
            text: The label text content.
            for_id: Optional element ID or FormComponent to associate with.
            **extra_settings: Additional HTML attributes.
        """
        self.text = text
        if isinstance(for_id, FormComponent):
            for_id = for_id.get_id()
        self.for_id = for_id
        self.extra_settings = extra_settings


@dataclass(repr=False)
class TextBox(FormComponent):
    """Text input field for single-line user input.

    Attributes:
        default_value: Optional initial value for the text box.
        kind: The HTML input type (text, password, email, etc.).
        tag: The HTML tag name, always 'input'.
    """

    default_value: Optional[str]
    kind: str

    tag = "input"
    SELF_CLOSING_TAG = True

    ARGUMENTS = [
        ComponentArgument("name"),
        ComponentArgument("default_value", kind="keyword", default_value=""),
        ComponentArgument("kind", kind="keyword", default_value="text"),
    ]

    RENAME_ATTRS = {"kind": "type", "default_value": "value"}
    # TODO: There are many more of these to add in, see URL below
    # https://developer.mozilla.org/en-US/docs/Web/HTML/Reference/Elements/input#attributes
    KNOWN_ATTRS = ["type", "name", "value", "alt"]
    DEFAULT_ATTRS = {"type": "text"}

    def __init__(
        self,
        name: str,
        default_value: Optional[Union[str, int, float]] = "",
        kind: str = "text",
        **extra_settings,
    ):
        validate_parameter_name(name, "TextBox")
        self.name = name
        self.kind = kind
        # TODO: Can validate for supported types (text, password, email, search, number, etc.)
        self.default_value = str(default_value) if default_value is not None else ""
        self.extra_settings = extra_settings


@dataclass(repr=False)
class TextArea(FormComponent):
    tag = "textarea"
    default_value: str

    COLLAPSE_WHITESPACE = True

    ARGUMENTS = [
        ComponentArgument("name"),
        ComponentArgument(
            "default_value", kind="keyword", is_content=True, default_value=""
        ),
    ]

    KNOWN_ATTRS = [
        "name",
        "rows",
        "cols",
        "autocomplete",
        "autofocus",
        "disabled",
        "placeholder",
        "readonly",
        "required",
    ]

    def __init__(
        self,
        name: str,
        default_value: Optional[Union[str, int, float]] = None,
        **kwargs,
    ):
        validate_parameter_name(name, "TextArea")
        self.name = name
        self.default_value = str(default_value) if default_value is not None else ""
        self.extra_settings = kwargs


@dataclass(repr=False)
class SelectBox(FormComponent):
    tag = "select"
    options: List[str]
    default_value: Optional[str]

    KNOWN_ATTRS = ["name"]
    ARGUMENTS = [
        ComponentArgument("name"),
        ComponentArgument("options"),
        ComponentArgument("default_value", kind="keyword", default_value=None),
    ]

    RENAME_ATTRS = {"default_value": "", "options": ""}

    def __init__(
        self,
        name: str,
        options: List[str],
        default_value: Optional[Union[str, int, float]] = None,
        **kwargs,
    ):
        """Initialize select box component.

        Args:
            name: The form field name.
            options: List of option values to display.
            default_value: Optional initially selected value.
            **kwargs: Additional HTML attributes.

        Raises:
            ValueError: If name is not a valid parameter name.
        """
        validate_parameter_name(name, "SelectBox")
        self.name = name
        self.options = [str(option) for option in options]
        self.default_value = str(default_value) if default_value is not None else ""
        self.extra_settings = kwargs

    def get_children(self, context) -> list[PageContent | RenderPlan]:
        children = []
        for option in self.options:
            option_attrs: dict[str, Any] = {"value": option}
            if option == self.default_value:
                option_attrs["selected"] = True
            children.append(
                RenderPlan(
                    kind="tag",
                    tag_name="option",
                    attributes=option_attrs,
                    children=[option],
                    known_attributes=["value", "selected"],
                )
            )

        return children


@dataclass(repr=False)
class CheckBox(FormComponent):
    default_value: bool

    tag = "input"
    KNOWN_ATTRS = ["type", "name", "checked"]

    ARGUMENTS = [
        ComponentArgument("name"),
        ComponentArgument("default_value", kind="keyword", default_value=False),
    ]
    RENAME_ATTRS = {"default_value": "checked"}
    DEFAULT_ATTRS = {"type": "checkbox"}

    def __init__(self, name: str, default_value: bool = False, **kwargs):
        """Initialize checkbox component.

        Args:
            name: The form field name.
            default_value: Whether initially checked. Defaults to False.
            **kwargs: Additional HTML attributes.

        Raises:
            ValueError: If name is not a valid parameter name.
        """
        validate_parameter_name(name, "CheckBox")
        self.name = name
        self.default_value = bool(default_value)
        self.extra_settings = kwargs

    def plan(self, context) -> RenderPlan:
        # Hidden input for unchecked state
        hidden_plan = RenderPlan(
            kind="tag",
            tag_name="input",
            attributes={
                "type": "hidden",
                "name": self.name,
                "value": "",
                "id": f"--drafter-hidden-{self.get_id()}",
            },
            self_closing=True,
            known_attributes=["type", "name", "value", "id"],
        )

        # Checkbox input
        checkbox_plan = self._plan_tag(context)

        return RenderPlan(kind="fragment", items=[hidden_plan, checkbox_plan])


@dataclass(repr=False)
class DateTimeInput(FormComponent):
    """
    A datetime-local input component for selecting both date and time.

    TODO: Handle __eq__ and __hash__

    Args:
       Input for selecting dates in YYYY-MM-DD format.

    Attributes:
        default_value: Optional default value in ISO 8601 format or date object.
        tag: The HTML tag name, always 'input'.
    """

    default_value: Union[str, None]

    tag = "input"
    SELF_CLOSING_TAG = True
    KNOWN_ATTRS = ["type", "name", "value"]

    ARGUMENTS = [
        ComponentArgument("name"),
        ComponentArgument("default_value", kind="keyword", default_value=None),
    ]
    DEFAULT_ATTRS = {"type": "datetime-local"}
    RENAME_ATTRS = {"default_value": "value"}

    def __init__(
        self, name: str, default_value: Union[str, None, datetime] = None, **kwargs
    ):
        validate_parameter_name(name, "DateTimeInput")
        self.name = name
        self.default_value = (
            default_value.isoformat(timespec="minutes")
            if isinstance(default_value, datetime)
            else str(default_value)
            if default_value is not None
            else None
        )
        self.extra_settings = kwargs


@dataclass(repr=False)
class DateInput(FormComponent):
    """
    A date input component for selecting dates.

    Args:
        name: The name of the form field
        default_value: Optional default value in ISO 8601 format (YYYY-MM-DD)
        kwargs: Additional HTML attributes
    """

    default_value: Union[str, None]

    tag = "input"
    SELF_CLOSING_TAG = True
    KNOWN_ATTRS = ["type", "name", "value"]
    DEFAULT_ATTRS = {"type": "date"}
    RENAME_ATTRS = {"default_value": "value"}

    ARGUMENTS = [
        ComponentArgument("name"),
        ComponentArgument("default_value", kind="keyword", default_value=None),
    ]

    def __init__(
        self,
        name: str,
        default_value: Union[str, None, datetime, date] = None,
        **kwargs,
    ):
        validate_parameter_name(name, "DateInput")
        self.name = name
        self.default_value = (
            default_value.isoformat()
            if isinstance(default_value, (datetime, date))
            else str(default_value)
            if default_value is not None
            else None
        )
        self.extra_settings = kwargs


@dataclass(repr=False)
class TimeInput(FormComponent):
    """
    A time input component for selecting times.

    Args:
        name: The name of the form field
        default_value: Optional default value in ISO 8601 format (HH:MM or HH:MM:SS)
        kwargs: Additional HTML attributes
    """

    default_value: Union[str, None]

    tag = "input"
    SELF_CLOSING_TAG = True
    KNOWN_ATTRS = ["type", "name", "value"]
    RENAME_ATTRS = {"default_value": "value"}

    ARGUMENTS = [
        ComponentArgument("name"),
        ComponentArgument("default_value", kind="keyword", default_value=None),
    ]

    DEFAULT_ATTRS = {"type": "time"}

    def __init__(
        self, name: str, default_value: Union[str, None, time] = None, **kwargs
    ):
        validate_parameter_name(name, "TimeInput")
        self.name = name
        self.default_value = (
            default_value.isoformat()
            if isinstance(default_value, time)
            else str(default_value)
            if default_value is not None
            else None
        )
        self.extra_settings = kwargs
