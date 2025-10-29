from dataclasses import dataclass
import html
from typing import List, Optional
from drafter.components.page_content import PageContent
from drafter.components.utilities.validation import validate_parameter_name


@dataclass
class TextBox(PageContent):
    name: str
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
        extra_settings = {}
        if self.default_value is not None:
            extra_settings["value"] = html.escape(self.default_value)
        parsed_settings = self.parse_extra_settings(**extra_settings)
        # TODO: investigate whether we need to make the name safer
        return f"<input type='{self.kind}' name='{self.name}' {parsed_settings}>"


@dataclass
class TextArea(PageContent):
    name: str
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


@dataclass
class SelectBox(PageContent):
    name: str
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


@dataclass
class CheckBox(PageContent):
    EXTRA_ATTRS = ["checked"]
    name: str
    default_value: bool

    def __init__(self, name: str, default_value: bool = False, **kwargs):
        validate_parameter_name(name, "CheckBox")
        self.name = name
        self.default_value = bool(default_value)
        self.extra_settings = kwargs

    def __str__(self) -> str:
        parsed_settings = self.parse_extra_settings(**self.extra_settings)
        checked = "checked" if self.default_value else ""
        return (
            f"<input type='hidden' name='{self.name}' value='' {parsed_settings}>"
            f"<input type='checkbox' name='{self.name}' {checked} value='checked' {parsed_settings}>"
        )
