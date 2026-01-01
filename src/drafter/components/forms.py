from dataclasses import dataclass
import html
from typing import List, Optional
from drafter.components.page_content import Component
from drafter.components.utilities.validation import validate_parameter_name


class FormComponent(Component):
    name: str

    def handle_aria(self, extra_settings: dict) -> None:
        if "aria-label" not in extra_settings:
            extra_settings["aria-label"] = self.name


@dataclass
class TextBox(FormComponent):
    kind: str
    default_value: Optional[str]

    def __init__(
        self,
        name: str,
        default_value: Optional[str] = None,
        kind: str = "text",
        **kwargs,
    ):
        validate_parameter_name(name, "TextBox")
        self.name = name
        self.kind = kind
        self.default_value = str(default_value) if default_value is not None else ""
        self.extra_settings = kwargs

    def __str__(self) -> str:
        extra_settings = dict(self.extra_settings)
        if self.default_value is not None:
            extra_settings["value"] = html.escape(self.default_value)
        self.handle_aria(extra_settings)
        parsed_settings = self.parse_extra_settings(**extra_settings)
        # TODO: investigate whether we need to make the name safer
        return f"<input type='{self.kind}' name='{self.name}' {parsed_settings}>"

    def __repr__(self) -> str:
        """
        name: str,
        default_value: Optional[str] = None,
        kind: str = "text",
        """
        pieces = [repr(self.name)]
        if self.default_value != "":
            pieces.append(repr(self.default_value))
        if self.kind != "text":
            pieces.append(repr(self.kind))
        for key, value in self.extra_settings.items():
            pieces.append(f"{key}={repr(value)}")
        return f"TextBox({', '.join(pieces)})"


@dataclass
class TextArea(FormComponent):
    default_value: str
    EXTRA_ATTRS = [
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

    def __str__(self) -> str:
        parsed_settings = self.parse_extra_settings(**self.extra_settings)
        return f"<textarea name='{self.name}' {parsed_settings}>{html.escape(self.default_value)}</textarea>"

    def __repr__(self) -> str:
        """
        name: str,
        default_value: Optional[str] = None,
        kind: str = "text",
        """
        pieces = [repr(self.name)]
        if self.default_value != "":
            pieces.append(repr(self.default_value))
        for key, value in self.extra_settings.items():
            pieces.append(f"{key}={repr(value)}")
        return f"TextArea({', '.join(pieces)})"


@dataclass
class SelectBox(FormComponent):
    options: List[str]
    default_value: Optional[str]

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

    def __str__(self) -> str:
        extra_settings = {}
        if self.default_value is not None:
            extra_settings["value"] = html.escape(self.default_value)
        parsed_settings = self.parse_extra_settings(**extra_settings)
        options = "\n".join(
            f"<option {'selected' if option == self.default_value else ''} "
            f"value='{html.escape(option)}'>{option}</option>"
            for option in self.options
        )
        return f"<select name='{self.name}' {parsed_settings}>{options}</select>"

    def __repr__(self) -> str:
        """
        name: str,
        options: List[str],
        default_value: Optional[str] = None,
        """
        pieces = [repr(self.name), repr(self.options)]
        if self.default_value != "":
            pieces.append(repr(self.default_value))
        for key, value in self.extra_settings.items():
            pieces.append(f"{key}={repr(value)}")
        return f"SelectBox({', '.join(pieces)})"


@dataclass
class CheckBox(FormComponent):
    EXTRA_ATTRS = ["checked"]
    default_value: bool

    def __init__(self, name: str, default_value: bool = False, **kwargs):
        validate_parameter_name(name, "CheckBox")
        self.name = name
        self.default_value = bool(default_value)
        self.extra_settings = kwargs

    def __str__(self) -> str:
        extra_settings = dict(self.extra_settings)
        self.handle_aria(extra_settings)
        parsed_settings = self.parse_extra_settings(**extra_settings)
        checked = "checked" if self.default_value else ""
        return (
            f"<input type='hidden' name='{self.name}' value='' {parsed_settings}>"
            f"<input type='checkbox' name='{self.name}' {checked} value='checked' {parsed_settings}>"
        )

    def __repr__(self) -> str:
        pieces = [repr(self.name)]
        if self.default_value:
            pieces.append(f"default_value={repr(self.default_value)}")
        for key, value in self.extra_settings.items():
            pieces.append(f"{key}={repr(value)}")
        return f"CheckBox({', '.join(pieces)})"


@dataclass
class Label(Component):
    """
    A label component for form fields. Can be associated with a form element using the for_id parameter.
    
    :param text: The text content of the label
    :param for_id: Optional ID of the form element this label is for
    """
    text: str
    for_id: Optional[str] = None
    
    def __init__(self, text: str, for_id: Optional[str] = None, **kwargs):
        self.text = text
        self.for_id = for_id
        self.extra_settings = kwargs
    
    def __str__(self) -> str:
        extra_settings = dict(self.extra_settings)
        if self.for_id:
            extra_settings["for"] = self.for_id
        parsed_settings = self.parse_extra_settings(**extra_settings)
        return f"<label {parsed_settings}>{html.escape(self.text)}</label>"
    
    def __repr__(self) -> str:
        pieces = [repr(self.text)]
        if self.for_id:
            pieces.append(f"for_id={repr(self.for_id)}")
        for key, value in self.extra_settings.items():
            pieces.append(f"{key}={repr(value)}")
        return f"Label({', '.join(pieces)})"


# Datetime input components for handling date and time inputs

@dataclass
class DateTimeInput(FormComponent):
    """
    A datetime-local input component for selecting both date and time.
    
    :param name: The name of the form field
    :param default_value: Optional default value in ISO 8601 format (YYYY-MM-DDTHH:MM)
    :param kwargs: Additional HTML attributes
    """
    default_value: Optional[str]
    
    def __init__(self, name: str, default_value: Optional[str] = None, **kwargs):
        validate_parameter_name(name, "DateTimeInput")
        self.name = name
        self.default_value = default_value
        self.extra_settings = kwargs
    
    def __str__(self) -> str:
        extra_settings = dict(self.extra_settings)
        if self.default_value is not None:
            extra_settings["value"] = html.escape(self.default_value)
        self.handle_aria(extra_settings)
        parsed_settings = self.parse_extra_settings(**extra_settings)
        return f"<input type='datetime-local' name='{self.name}' {parsed_settings}>"
    
    def __repr__(self) -> str:
        pieces = [repr(self.name)]
        if self.default_value:
            pieces.append(repr(self.default_value))
        for key, value in self.extra_settings.items():
            pieces.append(f"{key}={repr(value)}")
        return f"DateTimeInput({', '.join(pieces)})"


@dataclass
class DateInput(FormComponent):
    """
    A date input component for selecting dates.
    
    :param name: The name of the form field
    :param default_value: Optional default value in ISO 8601 format (YYYY-MM-DD)
    :param kwargs: Additional HTML attributes
    """
    default_value: Optional[str]
    
    def __init__(self, name: str, default_value: Optional[str] = None, **kwargs):
        validate_parameter_name(name, "DateInput")
        self.name = name
        self.default_value = default_value
        self.extra_settings = kwargs
    
    def __str__(self) -> str:
        extra_settings = dict(self.extra_settings)
        if self.default_value is not None:
            extra_settings["value"] = html.escape(self.default_value)
        self.handle_aria(extra_settings)
        parsed_settings = self.parse_extra_settings(**extra_settings)
        return f"<input type='date' name='{self.name}' {parsed_settings}>"
    
    def __repr__(self) -> str:
        pieces = [repr(self.name)]
        if self.default_value:
            pieces.append(repr(self.default_value))
        for key, value in self.extra_settings.items():
            pieces.append(f"{key}={repr(value)}")
        return f"DateInput({', '.join(pieces)})"


@dataclass
class TimeInput(FormComponent):
    """
    A time input component for selecting times.
    
    :param name: The name of the form field
    :param default_value: Optional default value in ISO 8601 format (HH:MM or HH:MM:SS)
    :param kwargs: Additional HTML attributes
    """
    default_value: Optional[str]
    
    def __init__(self, name: str, default_value: Optional[str] = None, **kwargs):
        validate_parameter_name(name, "TimeInput")
        self.name = name
        self.default_value = default_value
        self.extra_settings = kwargs
    
    def __str__(self) -> str:
        extra_settings = dict(self.extra_settings)
        if self.default_value is not None:
            extra_settings["value"] = html.escape(self.default_value)
        self.handle_aria(extra_settings)
        parsed_settings = self.parse_extra_settings(**extra_settings)
        return f"<input type='time' name='{self.name}' {parsed_settings}>"
    
    def __repr__(self) -> str:
        pieces = [repr(self.name)]
        if self.default_value:
            pieces.append(repr(self.default_value))
        for key, value in self.extra_settings.items():
            pieces.append(f"{key}={repr(value)}")
        return f"TimeInput({', '.join(pieces)})"
