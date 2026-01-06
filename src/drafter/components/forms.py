from dataclasses import dataclass
from datetime import datetime, date, time
import html
from typing import List, Optional, Union, Any
from drafter.components.page_content import Component, ComponentArgument, PageContent
from drafter.components.planning.render_plan import RenderPlan
from drafter.components.utilities.validation import validate_parameter_name


class FormComponent(Component):
    name: str

    def handle_aria(self, attributes: dict) -> None:
        if "aria-label" not in attributes:
            attributes["aria-label"] = self.name

    def get_attributes(self, context) -> dict:
        attrs = super().get_attributes(context)
        self.handle_aria(attrs)
        return attrs

    def get_id(self) -> str:
        return self.extra_settings.get("id", self.name)


@dataclass(repr=False)
class Label(Component):
    """
    A label component for form fields.
    Can be associated with a form element using the for_id parameter.

    :param text: The text content of the label
    :param for_id: Optional ID of the form element this label is for
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
        self.text = text
        if isinstance(for_id, FormComponent):
            for_id = for_id.get_id()
        self.for_id = for_id
        self.extra_settings = extra_settings


@dataclass(repr=False)
class TextBox(FormComponent):
    default_value: Optional[str]
    kind: str

    tag = "input"
    SELF_CLOSING_TAG = True

    ARGUMENTS = [
        ComponentArgument("name"),
        ComponentArgument("default_value", kind="keyword", default_value=None),
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
        default_value: Optional[str] = None,
        kind: str = "text",
        **extra_settings,
    ):
        validate_parameter_name(name, "TextBox")
        self.name = name
        self.kind = kind
        # TODO: Can validate for supported types (text, password, email, search, number, etc.)
        self.default_value = default_value
        self.extra_settings = extra_settings


@dataclass(repr=False)
class TextArea(FormComponent):
    tag = "textarea"
    default_value: str

    ARGUMENTS = [
        ComponentArgument("name"),
        ComponentArgument(
            "default_value", kind="keyword", is_content=True, default_value=None
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

    def __init__(self, name: str, default_value: Optional[str] = None, **kwargs):
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
        default_value: Optional[str] = None,
        **kwargs,
    ):
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

    :param name: The name of the form field
    :param default_value: Optional default value in ISO 8601 format (YYYY-MM-DDTHH:MM) or python datetime
    :param kwargs: Additional HTML attributes
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

    :param name: The name of the form field
    :param default_value: Optional default value in ISO 8601 format (YYYY-MM-DD)
    :param kwargs: Additional HTML attributes
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

    :param name: The name of the form field
    :param default_value: Optional default value in ISO 8601 format (HH:MM or HH:MM:SS)
    :param kwargs: Additional HTML attributes
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
